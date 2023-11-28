from sympy import *

# 在一张 x, y 的坐标图中
# 在 x 轴上确定两个点的  坐标和 对应的 x 轴 label 数值 (x1, y1, l1) (x2, y2, l2)
# 在 y 轴上确定两个点的  坐标和 对应的 y 轴 label 数值 (x3, y3, l3) (x4, y4, l4)
# 求图中任意一点 (px, py) 的 真实数值 (x, y)


# x1, y1, x2, y2, x3, y3, x4, y4, px, py, l1, l2, l3, l4 = symbols(
#     "p1[0] p1[1] p2[0] p2[1] p3[0] p3[1] p4[0] p4[1] p[0] p[1] l1 l2 l3 l4"
# )

x1, y1, x2, y2, x3, y3, x4, y4, px, py, l1, l2, l3, l4 = symbols(
    "x1 y1 x2 y2 x3 y3 x4 y4 px py l1 l2 l3 l4"
)

A = Matrix([[x2 - x1, x4 - x3], [y2 - y1, y4 - y3]])

B = Matrix([[y2 - y1, x1 - x2], [y4 - y3, x3 - x4]])
C = Matrix([[x3 * (y2 - y1) - y3 * (x2 - x1)], [x1 * (y4 - y3) - y1 * (x4 - x3)]])


O = B.inv() @ C

D = Matrix([[px - O[0]], [py - O[1]]])

res = A.inv() @ D

x = res[0] * (l2 - l1) + l1
y = res[1] * (l4 - l3) + l3

print(simplify(x))
print()
print(simplify(y))
