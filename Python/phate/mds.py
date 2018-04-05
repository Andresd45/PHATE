# author: Daniel Burkhardt <daniel.burkhardt@yale.edu>
# (C) 2017 Krishnaswamy Lab GPLv2

from sklearn.manifold import MDS
from sklearn.decomposition import PCA
from scipy.spatial.distance import pdist
from scipy.spatial.distance import squareform
import numpy as np

# Fast classical MDS using random svd


def cmdscale_fast(D, ndim):
    """
    Fast CMDS using randomm SVD
    """
    D = D**2
    D = D - D.mean(axis=0)[None, :]
    D = D - D.mean(axis=1)[:, None]

    pca = PCA(n_components=ndim, svd_solver='randomized')
    Y = pca.fit_transform(D)

    return Y


def embed_MDS(X, ndim=2, how='metric', distance_metric='euclidean', njobs=1, seed=None):
    """
    Performs classic, metric, and non-metric MDS

    Parameters
    ----------
    X: ndarray [n_samples, n_samples]
        2 dimensional input data array with n_samples
        embed_MDS does not check for matrix squareness, but this is nescessary for PHATE

    n_dim : int, optional, default: 2
        number of dimensions in which the data will be embedded

    how : string, optional, default: 'classic'
        choose from ['classic', 'metric', 'nonmetric']
        which MDS algorithm is used for dimensionality reduction

    distance_metric : string, optional, default: 'euclidean'
        choose from [‘cosine’, ‘euclidean’]
        distance metric for MDS

    njobs : integer, optional, default: 1
        The number of jobs to use for the computation.
        If -1 all CPUs are used. If 1 is given, no parallel computing code is used at all, which is useful for debugging.
        For n_jobs below -1, (n_cpus + 1 + n_jobs) are used. Thus for n_jobs = -2, all CPUs but one are used

    seed: integer or numpy.RandomState, optional
        The generator used to initialize SMACOF (metric, nonmetric) MDS
        If an integer is given, it fixes the seed
        Defaults to the global numpy random number generator

    Returns
    -------
    Y : ndarray [n_samples, n_dim]
        low dimensional embedding of X using MDS
    """

    # MDS embeddings, each gives a different output.
    X_dist = squareform(pdist(X, distance_metric))

    if how == 'classic':
        # classical MDS as defined in cmdscale
        #Y = cmdscale(X_dist)[0][:,:ndim]
        Y = cmdscale_fast(X_dist, ndim)
    elif how == 'metric':
        # First compute CMDS
        Y_cmds = cmdscale_fast(X_dist, ndim)
        # Metric MDS from sklearn
        Y = MDS(n_components=ndim, metric=True, max_iter=3000, eps=1e-12,
                dissimilarity="precomputed", random_state=seed, n_jobs=njobs,
                n_init=1).fit_transform(X_dist, init=Y_cmds)
    elif how == 'nonmetric':
        # First compute CMDS
        Y_cmds = cmdscale_fast(X_dist, ndim)
        # Then compute Metric MDS
        Y_mmds = MDS(n_components=ndim, metric=True, max_iter=3000, eps=1e-12,
                     dissimilarity="precomputed", random_state=seed, n_jobs=njobs,
                     n_init=1).fit_transform(X_dist, init=Y_cmds)
        # Nonmetric MDS from sklearn using metric MDS as an initialization
        Y = MDS(n_components=ndim, metric=False, max_iter=3000, eps=1e-12,
                dissimilarity="precomputed", random_state=seed, n_jobs=njobs,
                n_init=1).fit_transform(X_dist, init=Y_mmds)
    else:
        raise ValueError(
            "Allowable 'how' values for MDS: 'classic', 'metric', or 'nonmetric'. '%s' was passed." % (how))
    return Y
