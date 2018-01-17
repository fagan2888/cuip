from __future__ import print_function

import os
import cPickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
# from fastdtw import fastdtw
from sklearn.cluster import KMeans
from sklearn.externals import joblib
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import silhouette_score, confusion_matrix
from scipy.ndimage.filters import gaussian_filter1d, gaussian_filter
# from tsfresh import extract_features
# from tsfresh.feature_extraction.settings import EfficientFCParameters
plt.style.use("ggplot")

def traintestsplit(lc, train_split=0.7, seed=5):
    """Split sources into training and testing sets, where each bbl is only
    assigned to either the training or test set.
    Args:
        lc (object) - LightCurve object.
        train_split (float) - proportion of training set.
    Returns:
        train (list) - List of sources' idx.
        test (list) - List of sources' idx.
    """
    np.random.seed(seed)
    # -- Count the number of sources for each bbl.
    bbl = Counter(lc.coords_bbls.values())
    key = bbl.keys()
    np.random.shuffle(key)
    # -- Dictionaries to store src count and list of bbls.
    trn = {"count": 0., "bbls": []}
    tst = {"count": 0., "bbls": []}
    # -- For each bbl key add to training or test set.
    for kk in key:
        vv = bbl[kk]
        # -- If it's the first record add a records to the train set.
        if trn["count"] == 0.:
            trn["bbls"].append(kk)
            trn["count"] = trn["count"] + vv
        # -- If train set is above 0.7 of total, add to test set.
        elif trn["count"] / (trn["count"] + tst["count"]) > train_split:
            tst["bbls"].append(kk)
            tst["count"] = tst["count"] + vv
        # -- Else add to train set.
        else:
            trn["bbls"].append(kk)
            trn["count"] = trn["count"] + vv
    # -- Map source indexes based on bbls.
    traink = [src for src, bbl in lc.coords_bbls.items() if bbl in trn["bbls"]]
    traink = filter(lambda x: x in lc.coords_cls.keys(), traink)
    trainv = [lc.coords_cls[ii] for ii in traink]
    testk  = [src for src, bbl in lc.coords_bbls.items() if bbl in tst["bbls"]]
    testk  = filter(lambda x: x in lc.coords_cls.keys(), testk)
    testv  = [lc.coords_cls[ii] for ii in testk]
    # -- Print status.
    print("Train Set: {} res, {} non-res".format(
        sum(np.array(trainv) == 1), sum(np.array(trainv) != 1)))
    print("Test Set: {} res, {} non-res".format(
        sum(np.array(testv) == 1), sum(np.array(testv) != 1)))
    return [[traink, trainv], [testk, testv]]


def stack_nights(path):
    """Load detrended ligtcurves and stack if there are no masked values.
    Args:
        path (str) - folder with detrended .npy files.
    Returns:
        data (dict) - dict of {pd.datetime: np.ma.array} pairs.
    """
    # -- Collect filenames at provided path.
    dtrend_fnames = filter(lambda x: x.startswith("detrend"), os.listdir(path))
    # -- Stack dtrended lightcurves to
    data = {}
    for fname in dtrend_fnames:
        tmp = np.load(os.path.join(path, fname))
        if (tmp.mask.sum() == 0) & (tmp.shape[0] > 2690):
            date = pd.datetime.strptime(fname[10:-4], "%Y-%m-%d")
            data[date] = tmp
    return data


def split_data(data, traink, testk, downsample=30, ndays=74):
    """Stack data and split into train and test sets.
    Args:
        data (dict) - dict of {pd.datetime: np.ma.array} pairs.
        traink (list) - list of train idxs.
        testk (list) - list of test idxs.
    Return:
        train (array) - 2D array, each training sources time series.
        test (array) - 2D array, each test sources time series.
        ndays (int) - number of days split into train/test sets.
    """
    # -- Stack the data in numpy cube.
    arr_len = 2692
    stack = np.dstack([arr.data[:arr_len] for arr in data.values()])[:, :, :ndays]
    # -- Split data into training and testing sets.
    train = np.vstack(stack[:, np.array(traink) - 1].T)
    test  = np.vstack(stack[:, np.array(testk) -1].T)
    if downsample: # -- If downsampling.
        # -- Define the padding size required.
        pad   = int(np.ceil(arr_len / float(downsample)) * downsample - arr_len)
        # -- Add padding to train/test and take the mean over N values.
        train = np.append(train, np.zeros((train.shape[0], pad)) * np.NaN, axis=1)
        train = np.nanmean(train.reshape(-1, 30), axis=1).reshape(-1, 90)
        test  = np.append(test, np.zeros((test.shape[0], pad)) * np.NaN, axis=1)
        test  = np.nanmean(test.reshape(-1, 30), axis=1).reshape(-1, 90)
    # -- Define the number of days in the dataset.
    ndays = stack.shape[-1]
    return [train, test, ndays]


def rf_classifier(fpath, train, trainv, test, testv, ndays, bool_label=True,
                  njobs=-1, load=True):
    """"""
    # -- Training and testing labels for each source.
    train_labels = np.array(trainv * ndays)
    # -- If bool_label, convert to True for residential and False else.
    if bool_label:
        train_labels = (train_labels == 1).astype(int)
    if load: # -- Load existing classifier.
        clf = joblib.load(fpath)
    else: # -- Fit a classifier.
        clf = RandomForestClassifier(n_estimators=1000, random_state=0,
            class_weight="balanced", n_jobs=njobs)
        # params = {"class_weight": ("balanced")}
        # clf = GridSearchCV(clf, params)
        clf.fit(train, train_labels)
        joblib.dump(clf, fpath)
    return clf


def votes_comparison(preds, testv, ndays, split=0.5, pprint=True):
    """"""
    # -- Take the mean over each source and bool split.
    votes = np.array(np.split(preds, ndays)).mean(axis=0) > split
    # -- Compare actual labels to voted labels.
    comp = zip(np.array(testv) == 1, votes)
    # -- Calculate overall, residential, and non-residential accuracy.
    acc = sum([k == v for k, v in comp]) * 1. / len(comp)
    res_acc = (sum([k == v for k, v in comp if k == True]) * 1. /
               len(filter(lambda x: x[0] == True, comp)))
    non_res_acc = (sum([k == v for k, v in comp if k == False]) * 1. /
                   len(filter(lambda x: x[0] == False, comp)))
    # -- Print results.
    if pprint:
        print("Split: {}, Acc.: {:.2f}, Res. Acc.: {:.2f}, Non-Res. Acc.: {:.2f}" \
            .format(split, acc * 100, res_acc * 100, non_res_acc * 100))
    return([acc, res_acc, non_res_acc])


def resample_vals(results):
    """"""
    np.random.seed(5)
    data = []
    # -- Reshape predictions into 2D array.
    vals = results["preds"].reshape(results["ndays"], -1)
    # -- Sample nn days of preds.
    for nn in np.array(range(vals.shape[0])) + 1:
        # -- Do so 1000 times.
        for _ in range(100):
            # -- Randomly select nn idxs,
            idx = np.random.randint(vals.shape[0], size=nn)
            # -- Select rows corresponding to idx.
            val = vals[idx, :]
            # -- Test all 0.05 breaks and save most accurate split.
            max_res = [0, 0, 0]
            split = 0
            # -- Print status.
            print("Sampling {} days ({}/{}).                                 " \
                .format(nn, _ + 1, 100), end="\r")
            sys.stdout.flush()
            for ii in np.array(range(20)) / 20.:
                res = votes_comparison(val.reshape(-1), results["testv"], nn,
                    ii, pprint=False)
                if res[0] > max_res[0]:
                    max_res = res
                    split = ii
            # -- Append values for max accuracy to data.
            acc, res_acc, non_res_acc = max_res
            data.append([nn, split, acc, res_acc, non_res_acc])
    return data


def plot_sampling_result(npy_path):
    """"""
    # -- Load sampling data in DataFrame.
    cols = ["N", "split", "acc", "res_acc", "nres_acc"]
    df = pd.DataFrame(np.load(npy_path), columns=cols)
    # -- Create figure.
    fig, axes = plt.subplots(ncols=2, nrows=2, figsize=(10, 5), sharex=True)
    # -- Plot mean overall accuracy.
    fig.axes[0].plot(df.groupby("N").mean()["acc"])
    fig.axes[0].set_ylabel("Overall Accuracy")
    # -- Plot mean residential accuracy.
    fig.axes[1].plot(df.groupby("N").mean()["res_acc"])
    fig.axes[1].set_ylabel("Residential Accuracy")
    # -- Plot mean non-residential accuracy.
    fig.axes[2].plot(df.groupby("N").mean()["nres_acc"])
    fig.axes[2].set_ylabel("Non-Residential Accuracy")
    fig.axes[2].set_xlabel("Nights")
    # -- Plot the mean best voting split.
    fig.axes[3].plot(df.groupby("N").mean()["split"])
    fig.axes[3].set_ylabel("Best Voting Split")
    fig.axes[3].set_xlabel("Nights")
    plt.tight_layout()
    plt.show()


def main(lc, rf_file, downsample=False, load=True):
    """"""
    # -- Split keys into train and test set,
    [traink, trainv], [testk, testv] = traintestsplit(lc)
    # -- Load data into and 3D numpy array.
    data = stack_nights(os.path.join(lc.path_out, "onsoffs"))
    # -- Split data into train and test (optionally downsample).
    train, test, ndays = split_data(data, traink, testk, downsample)
    # -- Train random forest and predict.
    clf = rf_classifier(rf_file, train, trainv, test, testv, ndays, load=load)
    preds = clf.predict(test)
    # -- Check if voting changes the results with various break points.
    print("Vote Comparison:")
    for ii in np.array(range(20)) / 20.:
        votes_comparison(preds, testv, ndays, ii)
    print(confusion_matrix((np.array(testv * ndays) == 1).astype(int), preds))
    return({"traink": traink, "trainv": trainv, "testk": testk, "testv": testv,
            "data": data, "train": train, "test": test, "ndays": ndays,
            "clf": clf, "preds": preds})


if __name__ == "__main__":
    rf_file = os.path.join(lc.path_out, "estimators", "rf_clf_src_7030_1000est_20180116.pkl")
    results = main(lc, rf_file, False, True)
