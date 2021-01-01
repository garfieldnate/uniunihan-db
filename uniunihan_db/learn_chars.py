import argparse
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

import pandas as pd
import wittgenstein as lw

# from sklearn import tree
# from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.multiclass import OneVsRestClassifier

# from sklearn.preprocessing import LabelEncoder

# TODO: putting logging config in shared file
logging.basicConfig(
    level=os.environ.get("LOGLEVEL", "INFO"),
    format="[%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)

PROJECT_DIR = Path(__file__).parents[1]

DATA_DIR = PROJECT_DIR / "data"


@dataclass
class Profile:
    X_suffixes: List[str]
    y: str

    def X_includes(self, feat_name):
        feat_name = str(feat_name)
        return any((feat_name.startswith(suffix) for suffix in self.X_suffixes))


profiles = {
    "ids2jp": Profile(["ids_"], "jp_surface"),
    "ids2zh": Profile(["ids_"], "zh_surface"),
    "ids2zhNoTone": Profile(["ids_"], "zh_tone_stripped"),
    "jp2zh": Profile(["jp_"], "zh_surface"),
    "jp2zhNoTone": Profile(["jp_"], "zh_tone_stripped"),
    "jpIds2zh": Profile(["jp_", "ids_"], "zh_surface"),
    "jpIds2zhNoTone": Profile(["jp_", "ids_"], "zh_tone_stripped"),
}

parser = argparse.ArgumentParser()
parser.add_argument("feature_file")
parser.add_argument(
    "-p",
    "--profile",
    # sanity check against Heisig Volume II
    default="ids2jp",
    choices=profiles.keys(),
    help="Training/prediction profile; input can be IDS or pronunciation data for Japanese, and output can be Japanese or Chinese (Mandarin) pronunciations.",
)


def learn(raw_data, profile_name):
    profile = profiles[profile_name]
    log.info(f"Using profile {profile}")

    log.info("Constructing data set...")
    # print(raw_data)
    # print([feats for feats in raw_data if profile.y in feats])
    # filtered = pd.DataFrame([feats for feats in raw_data if profile.y in feats])
    # print(filtered)
    filtered = raw_data

    all_feats = []
    for feat in filtered.columns:
        if profile.X_includes(feat):
            all_feats.append(feat)
    X = filtered[all_feats]
    # print(X.dtypes)
    y = filtered[profile.y]
    # print(y.dtypes)
    # print(data[profile.y])

    # X_string = []
    # y_string = []
    # for feats in raw_data:
    #     if profile.y not in feats:
    #         # for ids2jp, this is Heisig chapter 4
    #         log.info(f"Character {feats['char']} has no attribute {profile.y}")
    #         continue
    #     y_string.append(feats[profile.y])
    #     # get values for features specified in profile
    #     filtered_X = {k: v for k, v in feats.items() if profile.X_includes(k)}
    #     if not filtered_X:
    #         continue
    #     X_string.append(filtered_X)

    # feat_encoder = DictVectorizer()
    # X = feat_encoder.fit_transform(X_string)
    # print(X)
    # print(feat_encoder.inverse_transform(X[0]))

    # label_encoder = LabelEncoder()
    # y = label_encoder.fit_transform(y_string)
    # print(y)
    # print(label_encoder.inverse_transform(y))

    log.info("Learning rules...")
    clf = OneVsRestClassifier(lw.RIPPER())

    # log.info("Learning decision tree...")
    # clf = tree.DecisionTreeClassifier(max_depth=3)

    clf = clf.fit(X, y)  # ,class_feat=profile.y
    pred_y = clf.predict(X)
    print("Accuracy on training set:", accuracy_score(y, pred_y))
    print("Precision on training set:", precision_score(y, pred_y))
    print("Recall on training set:", recall_score(y, pred_y))

    # print(clf.ruleset_.out_pretty())

    # print(f"Depth: {clf.get_depth()}")

    # plot_file_name = DATA_DIR / (profile_name + ".dot")
    # log.info(f"Writing plot to {plot_file_name}...")
    # tree.export_graphviz(
    #     clf,
    #     out_file=str(plot_file_name),
    #     feature_names=feat_encoder.get_feature_names(),
    #     class_names=label_encoder.classes_,
    #     filled=True,
    #     rounded=True,
    #     special_characters=True,
    # )


def main():
    args = parser.parse_args()

    log.info("Reading feature file...")
    with open(args.feature_file) as f:
        data = json.load(f)
    data = pd.DataFrame(data).astype(str)
    log.info(f"Read features for {len(data)} characters")

    learn(data, args.profile)


if __name__ == "__main__":
    main()
