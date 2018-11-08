import abc
import torch
from . import util


class Manifold(metaclass=abc.ABCMeta):
    name = ''

    @abc.abstractmethod
    def check_dims(self, x):
        raise NotImplementedError

    def retr(self, x, u, t):
        return self._retr(x, u, t)

    def transp(self, x, u, v, t):
        return self._transp(x, u, v, t)

    def inner(self, x, u, v=None):
        if v is None:
            v = u
        return self._inner(x, u, v)

    def proju(self, x, u):
        return self._proju(x, u)

    def projx(self, x):
        return self._projx(x)

    @abc.abstractmethod
    def _retr(self, x, u, t):
        raise NotImplementedError

    @abc.abstractmethod
    def _transp(self, x, u, v, t):
        raise NotImplementedError

    @abc.abstractmethod
    def _inner(self, x, u, v):
        raise NotImplementedError

    @abc.abstractmethod
    def _proju(self, x, u):
        raise NotImplementedError

    @abc.abstractmethod
    def _projx(self, x):
        raise NotImplementedError

    def __repr__(self):
        return self.name + ' manifold'

    def __eq__(self, other):
        return type(self) is type(other)


class Rn(Manifold):
    name = 'Rn'

    def check_dims(self, x):
        return True

    def _retr(self, x, u, t):
        return x + t * u

    def _inner(self, x, u, v):
        return (u * v).sum(-1)

    def _proju(self, x, u):
        return u

    def _projx(self, x):
        return x

    def _transp(self, x, u, v, t):
        return v


class Stiefel(Manifold):
    name = 'Stiefel'

    def check_dims(self, x):
        return x.dim() >= 2

    def amat(self, x, u, project=True):
        if project:
            u = self.proju(x, u)
        return u @ x.transpose(-1, -2) - x @ u.transpose(-1, -2)

    def _proju(self, x, u):
        p = -0.5 * x @ x.transpose(-1, -2)
        p[..., range(x.shape[-2]), range(x.shape[-2])] += 1
        return p @ u

    def _projx(self, x):
        U, d, V = util.svd(x)
        return torch.einsum("...ik,...k,...jk->...ij", [U, torch.ones_like(d), V])

    def _retr(self, x, u, t):
        a = self.amat(x, u, project=False)
        rhs = x + t / 2 * a @ x
        lhs = -t / 2 * a
        lhs[..., range(a.shape[-2]), range(x.shape[-2])] += 1
        qx, _ = torch.gesv(rhs, lhs)
        return qx

    def _inner(self, x, u, v):
        return (u * v).sum([-1, -2])

    def _transp(self, x, u, v, t):
        a = self.amat(x, u, project=False)
        rhs = v + t / 2 * a @ v
        lhs = -t / 2 * a
        lhs[..., range(a.shape[-2]), range(x.shape[-2])] += 1
        qv, _ = torch.gesv(rhs, lhs)
        return qv
