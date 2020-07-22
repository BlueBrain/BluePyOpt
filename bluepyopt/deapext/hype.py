import numpy

def hypesub(l, A, actDim, bounds, pvec, alpha, k):

    h = numpy.zeros(l)
    i = numpy.argsort(A[:, actDim - 1])
    S = A[i]
    pvec = pvec[i]

    for i in range(1, S.shape[0] + 1):

        if i < S.shape[0]:
            extrusion = S[i, actDim - 1] - S[i - 1, actDim - 1]
        else:
            extrusion = bounds[actDim - 1] - S[i - 1, actDim - 1]

        if actDim == 1:
            if i > k:
                break
            if alpha[i - 1] >= 0:
                h[pvec[0:i]] += extrusion * alpha[i - 1]
        elif extrusion > 0.:
            h += extrusion * hypesub(l, S[0:i, :], actDim - 1, bounds,
                                     pvec[0:i], alpha, k)

    return h


def hypeIndicatorExact(points, bounds, k):
    """
    points: objectives (to be minimized),
    bounds: reference point,
    k: parameter of HypE

    Example: scores = hypeIndicatorExact([[1., 3.], [3., 1.]], [4., 4.], 1)
    """

    Ps = points.shape[0]
    if k < 0:
        k = Ps
    actDim = points.shape[1]
    pvec = numpy.arange(points.shape[0])

    alpha = []
    for i in range(1, k + 1):
        j = numpy.arange(1, i)
        alpha.append(numpy.prod((k - j) / (Ps - j) / i))
    alpha = numpy.asarray(alpha)

    return hypesub(points.shape[0], points, actDim, bounds, pvec, alpha, k)


def hypeIndicatorSampled(points, bounds, k, nrOfSamples):

    nrP = points.shape[0]
    dim = points.shape[1]
    F = numpy.zeros(nrP)

    BoxL = numpy.min(points, axis=0)

    alpha = []
    for i in range(1, k + 1):
        j = numpy.arange(1, i)
        alpha.append(numpy.prod((k - j) / (nrP - j) / i))
    alpha = numpy.asarray(alpha + [0.]*nrP)

    S = numpy.random.uniform(low=BoxL, high=bounds, size=(nrOfSamples, dim))


    dominated = numpy.zeros(nrOfSamples, dtype="uint")
    for j in range(1, nrP+1):
        B = S - points[j-1]
        ind = numpy.sum(B >= 0, axis=1) == dim
        dominated[ind] += 1

    for j in range(1, nrP+1):
        B = S - points[j-1]
        ind = numpy.sum(B >= 0, axis=1) == dim
        x = dominated[ind]
        F[j-1] = numpy.sum(alpha[x-1])

    F = F * numpy.prod(bounds - BoxL) / nrOfSamples

    return F

