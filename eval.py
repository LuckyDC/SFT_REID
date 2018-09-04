import os
import subprocess
import sys
import argparse

import scipy.io as sio
from collections import namedtuple
from utils.evaluation import eval_feature

DATA_ROOT = "/mnt/truenas/scratch/chuanchen.luo/data/reid/"
DatasetConfig = namedtuple("DatasetConfig", ["query", "gallery", "name"])

market = DatasetConfig(query=DATA_ROOT + "Market-1501-v15.09.15-ssd/query",
                       gallery=DATA_ROOT + "Market-1501-v15.09.15-ssd/bounding_box_test",
                       name="market")

duke = DatasetConfig(query=DATA_ROOT + "DukeMTMC-reID-ssd/query",
                     gallery=DATA_ROOT + "DukeMTMC-reID-ssd/bounding_box_test",
                     name="duke")

cuhk = DatasetConfig(query=DATA_ROOT + "cuhk03-np-ssd/labeled/query",
                     gallery=DATA_ROOT + "cuhk03-np-ssd/labeled/bounding_box_test",
                     name="cuhk")

msmt = DatasetConfig(query=DATA_ROOT + "MSMT17_V1-ssd/list_query.txt",
                     gallery=DATA_ROOT + "MSMT17_V1-ssd/list_gallery.txt",
                     name="msmt")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("gpu", default=0, type=int)
    parser.add_argument("model_path", type=str)
    args = parser.parse_args()

    model_path = args.model_path
    basename = os.path.splitext(os.path.basename(model_path))[0]
    prefix = "-".join(basename.split("-")[:-1])
    epoch_idx = int(basename.split("-")[-1])
    gpu = args.gpu
    dataset = model_path.split("/")[1]
    force_resize = True

    print("%s/%s-%d" % (dataset, prefix, epoch_idx))

    query_features_path = 'features/%s/query-%s.mat' % (dataset, prefix)
    gallery_features_path = "features/%s/gallery-%s.mat" % (dataset, prefix)

    config = eval(dataset)
    query = config.query
    gallery = config.gallery

    cmd = "python%c -m utils.extract --prefix %s --gpu-id %d --epoch-idx %d --query %s --gallery %s --dataset %s" % (
        sys.version[0], prefix, gpu, epoch_idx, query, gallery, dataset)

    subprocess.check_call(cmd.split(" "))

    assert os.path.exists(query_features_path) and os.path.exists(gallery_features_path)

    query_mat = sio.loadmat(query_features_path)
    gallery_mat = sio.loadmat(gallery_features_path)

    query_features = query_mat["feat"]
    query_ids = query_mat["ids"].squeeze()
    query_cam_ids = query_mat["cam_ids"].squeeze()

    gallery_features = gallery_mat["feat"]
    gallery_ids = gallery_mat["ids"].squeeze()
    gallery_cam_ids = gallery_mat["cam_ids"].squeeze()

    eval_feature(query_features, gallery_features, query_ids, query_cam_ids, gallery_ids, gallery_cam_ids,
                 metric="cosine")

    print("\n")

    cmd = "python%c -m post_processing.random_walk_feat %s %s" % (sys.version[0], dataset, prefix)
    subprocess.check_call(cmd.split(" "))