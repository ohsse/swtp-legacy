import numpy as np
from matplotlib import pyplot as plt
from scipy.interpolate import griddata
from sklearn.neighbors import KNeighborsRegressor


np.random.seed(100)
real_sample_size = 50
x = np.random.uniform(-2, 2, real_sample_size)
y = np.random.uniform(-1.3, 1.3, real_sample_size)
z = x * np.exp(-x ** 2 - y ** 2)

grid_size = 100
x_range = np.linspace(np.max(x), np.min(x), grid_size)
y_range = np.linspace(np.max(y), np.min(y), grid_size)
points = np.c_[x, y]
X, Y = np.meshgrid(x_range, y_range)
Z = griddata(points, z, (X, Y), method='cubic')

reg = KNeighborsRegressor(n_neighbors=5, weights='distance').fit(np.c_[X[Z==Z], Y[Z==Z]], Z[Z==Z])
fill_z = reg.predict(np.c_[X[Z!=Z], Y[Z!=Z]])
Z[Z!=Z] = fill_z

fig = plt.figure(figsize=(12, 8))
fig.set_facecolor('white')
ax = fig.add_subplot()
contour1 = ax.contour(X, Y, Z, levels=10, colors='k', linewidths=1, linestyles='--')  ## 등고선
contour2 = ax.contourf(X, Y, Z, levels=256, cmap='jet')

ax.clabel(contour1, contour1.levels, inline=True)  ## contour 라벨
fig.colorbar(contour2, shrink=0.5)  ## 컬러바 크기 축소 shrink

ax.scatter(x, y, color='k', alpha=0.5, s=10)

plt.show()



