import numpy as np
from matplotlib import pyplot as plt
from scipy.interpolate import griddata

np.random.seed(100)

## 관측 데이터
real_sample_size = 50
x = np.random.uniform(-2, 2, real_sample_size)
y = np.random.uniform(-2, 2, real_sample_size)
z = x * np.exp(-x ** 2 - y ** 2)
# z = x * np.exp(-x ** 2 - y ** 2) * 1000

## 관측 데이터 시각화
# fig = plt.figure(figsize=(8, 8))
# fig.set_facecolor('white')
# ax = fig.add_subplot()
# ax.scatter(x, y, color='k', alpha=0.5, s=10)
#
# plt.show()


## 관측된 데이터를 이용하여 격자 데이터 생성
grid_size = 100
x_range = np.linspace(-2.2, 2.2, grid_size)  ## x 범위
y_range = np.linspace(-2.2, 2.2, grid_size)  ## y 범위
X, Y = np.meshgrid(x_range, y_range)  ## XY 격자 데이터

fig, axs = plt.subplots(1, 3, figsize=(24, 8))
fig.set_facecolor('white')

# method_list = ['nearest', 'linear', 'cubic']
method_list = ['cubic']
for i, method in enumerate(method_list):
    ax = axs[i]
    Z = griddata(np.c_[x, y], z, (X, Y), method=method)  ## Z 격자 데이터
    # Z = griddata(np.c_[X, Y], Z, (X, Y), method=method)  ## Z 격자 데이터
    contour1 = ax.contour(X, Y, Z, levels=10, colors='k', linewidths=1, linestyles='--')  ## 등고선
    contour2 = ax.contourf(X, Y, Z, levels=256, cmap='jet')

    ax.clabel(contour1, contour1.levels, inline=True)  ## contour 라벨
    ax.scatter(x, y, color='k', alpha=0.5, s=5)  ## 산점도 추가
    # ax.scatter(X, Y, color='k', alpha=0.5, s=5)  ## 산점도 추가
    ax.set_title(method, fontsize=20)
plt.show()