import time

from dxGame.dx_core import *
import cv2, numpy as np


class Node:
    def __init__(self, x, y, parent=None):
        self.x = x  # 节点的x坐标
        self.y = y  # 节点的y坐标
        self.parent = parent  # 父节点
        self.g = 0  # 从起点到当前节点的实际代价
        self.h = 0  # 当前节点到目标节点的估计代价

    def __lt__(self, other):
        return self.h < other.h  # 当f相同时，优先以最小的预估代价优先排序堆栈，这样靠近目标的速度稍微快一些

    def f(self):
        return self.g + self.h


class A_START:
    def __init__(self):
        self.start_time = 0
        self.sum_time = 0
        self.deltas = [(0, 1, 10), (0, -1, 10), (1, 0, 10), (-1, 0, 10),  # 右、左、下、上
                       (-1, -1, 14), (-1, 1, 14), (1, -1, 14), (1, 1, 14)  # 左上、右上、左下、右下
                       ]
        # self.deltas = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    def a_star(self, matrix, _start, _target, rows=(), cols=()):
        """

        :param matrix: 地图矩阵
        :param start: 开始行列
        :param target: 结束行列
        :param rows: 限制地图范围行，默认不限制
        :param cols: 限制地图范围列，默认不限制
        :return:
        """
        # 初始化
        start = Node(*_start)
        target = Node(*_target)
        min_rows, min_cols = rows if rows else 0, cols if cols else 0
        max_rows, max_cols = matrix.shape[:2]
        open_set = []
        heapq.heappush(open_set, (start.f(), start))  # 使用优先队列存储节点，按f值从小到大排序
        close_list = np.zeros(matrix.shape[:2], dtype=bool)
        close_list[start.y, start.x] = True  # 起始点开始标记为以访问

        # 开始遍历
        while open_set:
            # 计数器 += 1  # 衡量算法的计算量
            _, current = heapq.heappop(open_set)  # 弹出f值最小的节点
            if current.x == target.x and current.y == target.y:  # 到达目标节点
                return self.reconstruct_path(current)

            for dx, dy, l in self.deltas:
                nx = current.x + dx
                ny = current.y + dy

                if min_rows <= ny < max_rows and min_cols <= nx < max_cols and not (close_list[ny, nx]) and matrix[
                    ny, nx]:  # 判断该邻居节点是否在范围内，且没有遍历过，且可达
                    neighbor = Node(nx, ny)
                    neighbor.g = current.g + l  # 更新邻居节点的实际代价
                    neighbor.h = self.manhattan_distance(neighbor, target)  # 计算邻居节点到目标节点的估计代价
                    neighbor.parent = current  # 设置邻居节点的父节点为当前节点
                    heapq.heappush(open_set, (neighbor.f(), neighbor))  # 将邻居节点加入待访问的节点集合中
                    close_list[ny, nx] = True  # 添加到代表已经计算过代价，需要加入到关闭列表，避免下次在计算和添加

        return None

    @staticmethod
    def manhattan_distance(node, target):
        x, y = abs(node.x - target.x), abs(node.y - target.y)
        if x <= y:
            return 14 * x + abs(x - y) * 10
        else:
            return 14 * y + abs(x - y) * 10

        # return abs(node.x - target.x) + abs(node.y - target.y)

    @staticmethod
    def reconstruct_path(node):
        path = []
        while node.parent is not None:
            path.append((node.x, node.y))
            node = node.parent
        return list(reversed(path))


# 直线转坐标列表
def bresenham_line(p1, p2):
    x0, y0 = p1
    x1, y1 = p2
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    steep = dy > dx
    if steep:
        x0, y0 = y0, x0
        x1, y1 = y1, x1
        dx, dy = dy, dx
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    error = dx // 2
    points = []
    x, y = x0, y0
    for _ in range(dx + 1):
        points.append((y, x) if steep else (x, y))
        error -= dy
        if error < 0:
            y += sy
            error += dx
        x += sx
    return points


def is_safe(map_matrix, points):
    for x, y in points:
        if not (0 <= x < map_matrix.shape[1] and 0 <= y < map_matrix.shape[0]):
            return False
        if map_matrix[y, x] == 0:
            return False
    return True


def 直线优化路径(path_list, map_matrix):
    s = time.time()
    new_path_list = copy.deepcopy(path_list)
    while True:
        start_index = 0  # 起始点索引
        step_index = 4  # 最短间隔
        next_index = start_index + step_index
        temp_del_index_list = []
        while True:
            x1, y1 = new_path_list[start_index]
            if next_index >= len(new_path_list):
                break
            x2, y2 = new_path_list[next_index]
            # 计算 x1,y1 到 x2,y2的直线经过的近似点位
            points = bresenham_line((x1, y1), (x2, y2))
            # 计算这些点是否越界，如果不越界，则继续增大step_index
            if is_safe(map_matrix, points):
                temp = list(range(start_index + 1, next_index))
                temp_del_index_list.extend(temp)
            start_index = next_index
            next_index = next_index + step_index
        for index in temp_del_index_list[::-1]:
            new_path_list.pop(index)
        if not temp_del_index_list:
            break
    print("直线优化路径耗时：", time.time() - s)
    return new_path_list

def 补充直线(path_list):
    new_path_list = []
    length= len(path_list) - 1
    if length <= 2:
        return path_list
    for index in range(length):
        p1 = path_list[index]
        p2 = path_list[index + 1]
        points = bresenham_line(p1, p2)
        new_path_list.extend(points)
    return new_path_list


import numpy as np


def 是否是直线(points, threshold=0.3):
    # 提取点集的x和y坐标
    x = np.array([p[0] for p in points])
    y = np.array([p[1] for p in points])

    # 最小二乘法拟合直线
    A = np.vstack([x, np.ones(len(x))]).T
    coeffs, residuals, rank, singular_values = np.linalg.lstsq(A, y,
                                                               rcond=None)  # 正确解包返回值
    k, b = coeffs  # coeffs是一个数组，包含斜率和截距

    # 计算各点到直线的平均垂直距离
    distances = np.abs(k * x - y + b) / np.sqrt(k ** 2 + 1)
    avg_distance = np.mean(distances)

    return avg_distance < threshold
def 获取骨干网A星轨迹(骨干网,start_loc,end_loc):
    def 找到最近的点(thinned, loc):
        if thinned is None:
            return [-1,-1]
        if thinned[loc[1], loc[0]]:
            return loc
        thinned[loc[1], loc[0]] = 0  # 排除自身
        white_points = np.argwhere(thinned == 255)
        white_points_xy = white_points[:, [1, 0]].astype(np.int32)
        target = np.array(loc, dtype=np.int32)  # 目标点坐标
        delta = white_points_xy - target  # # 差值矩阵计算（利用广播机制）‌
        sq_distances = np.sum(delta ** 2, axis=1)  # 计算每个点到目标点的距离‌
        min_index = np.argmin(sq_distances)  # 找到最近点索引
        loc2 = list(white_points_xy[min_index])
        return loc2
    start_loc2 = 找到最近的点(骨干网, start_loc)
    end_loc2 = 找到最近的点(骨干网, end_loc)
    ax = A_START()
    result1 = 补充直线([start_loc, start_loc2])
    result2 = ax.a_star(骨干网, start_loc2, end_loc2)
    result3 = 补充直线([end_loc2, end_loc])
    result = result1 + result2 + result3
    return result

def 取直线的最远一个坐标(points,threshold=0.3):
    if len(points) <2:
        return

    start = 0
    end = 1
    while True:
        res = 是否是直线(points[start:end],threshold)
        if not res:
            return end - 1
        end += 1
        if end >= len(points):
            return end - 1
def 获取下一个坐标位置(x1, y1, x2, y2, x3, y3, r):
    dx = x2 - x1
    dy = y2 - y1
    θ = math.atan2(dy, dx)
    x4, y4 = (x3 + r * math.cos(θ), y3 + r * math.sin(θ))
    return int(x4), int(y4)

if __name__ == '__main__':
    # # 示例：计算 (2,3) 到 (5,7) 的直线点坐标
    # p1, p2 = (2, 3), (88, 99)
    # points = bresenham_line(p1, p2)
    # print(points)
    # # 在 OpenCV 图像上绘制验证
    # img = np.zeros((100, 100, 3), dtype=np.uint8)
    # for (x, y) in points:
    #     cv2.circle(img, (x, y), 0, (0, 255, 0), -1)  # 绘制点
    # cv2.imshow("Line Points", img)
    # cv2.waitKey(0)
    # path_list = [(2, 3), (5, 7), (8, 9), (10, 11), (12, 13), (14, 15), (16, 17), (18, 19), (20, 21), (22, 23), (24, 25), (26, 27), (28, 29),(30, 31), (32, 33), (34,35)] # 生成一条弯曲路径
    # img = np.zeros((100, 100), dtype=np.uint8)
    # img[...] = 255
    # new_path_list = 直线优化路径(path_list,img)
    # print(new_path_list)

    # 示例：拟合点集 (1,1), (2,3), (3,2), (4,5), (5,7)
    # 示例用法
    # points = [(73, 392), (74, 391), (75, 390), (76, 389), (77, 388), (78, 387), (79, 386), (80, 386), (81, 385), (82, 384), (83, 383), (84, 382), (85, 381), (86, 380), (87, 379), (87, 379), (87, 378), (87, 377), ]  # 接近直线的点集
    # points = [(73, 392), (74, 391), (75, 390), (76, 389), (77, 388), (78, 387), (79, 386), (80, 386), (81, 385), (82, 384), (83, 383), (84, 382), (85, 381), (86, 380), (87, 379), (87, 379), (87, 378), (87, 377), (88, 376), (88, 375), (88, 374), (88, 373), (88, 372), (89, 371), (89, 370), (89, 369), (89, 368), (89, 367), (90, 366), (90, 365), (90, 364), (90, 364), (89, 363), (88, 362), (87, 361), (86, 361), (85, 360), (84, 359), (83, 358), (82, 357), (81, 356), (80, 355), (79, 355), (78, 354), (77, 353), (76, 352), (76, 352), (76, 351), (76, 350), (75, 349), (75, 348), (75, 347), (75, 346), (74, 345), (74, 344), (74, 343), (74, 342), (73, 341), (73, 340), (73, 339), (73, 338), (72, 337), (72, 336), (72, 336), (72, 335), (72, 334), (73, 333), (73, 332), (73, 331), (73, 330), (74, 329), (74, 328), (74, 327), (74, 326), (75, 325), (75, 324), (75, 323), (75, 322), (76, 321), (76, 320), (76, 319), (76, 318), (77, 317), (77, 316), (77, 315), (77, 314), (77, 313), (78, 312), (78, 311), (78, 310), (78, 309), (79, 308), (79, 307), (79, 306), (79, 305), (80, 304), (80, 303), (80, 302), (80, 301), (81, 300), (81, 299), (81, 298), (81, 297), (82, 296), (82, 295), (82, 294), (82, 293), (82, 292), (83, 291), (83, 290), (83, 289), (83, 288), (84, 287), (84, 286), (84, 285), (84, 284), (85, 283), (85, 282), (85, 281), (85, 280), (86, 279), (86, 278), (86, 277), (86, 276), (87, 275), (87, 274), (87, 273), (87, 273), (88, 272), (89, 271), (89, 270), (90, 269), (91, 268), (92, 267), (92, 266), (93, 265), (94, 264), (95, 263), (95, 262), (96, 261), (97, 260), (98, 259), (98, 258), (99, 257), (100, 256), (101, 255), (101, 254), (102, 253), (103, 252), (104, 251), (104, 250), (105, 249), (106, 248), (107, 247), (107, 246), (108, 245), (109, 244), (110, 243), (110, 242), (111, 241), (112, 240), (113, 239), (113, 238), (114, 237), (115, 236), (116, 235), (116, 234), (117, 233), (118, 232), (119, 231), (119, 230), (120, 229), (121, 228), (122, 227), (122, 226), (123, 225), (124, 224), (125, 223), (125, 222), (126, 221), (127, 220), (127, 220), (128, 219), (129, 218), (130, 218), (131, 217), (132, 216), (133, 215), (134, 214), (135, 213), (136, 213), (137, 212), (138, 211), (139, 210), (139, 210), (140, 209), (141, 208), (142, 207), (143, 207), (144, 206), (145, 205), (146, 204), (147, 203), (148, 202), (149, 201), (150, 201), (151, 200), (152, 199), (153, 198), (153, 198), (154, 197), (155, 196), (156, 196), (157, 195), (158, 194), (159, 193), (160, 192), (161, 192), (162, 191), (163, 190), (164, 189), (165, 188), (166, 187), (167, 187), (168, 186), (169, 185), (169, 185), (170, 184), (170, 183), (171, 182), (172, 181), (173, 180), (173, 179), (174, 178), (175, 177), (176, 176), (176, 175), (177, 174), (178, 173), (179, 172), (179, 171), (180, 170), (181, 169), (181, 169), (182, 169), (183, 169), (184, 169), (185, 169), (186, 169), (187, 170), (188, 170), (189, 170), (190, 170), (191, 170), (192, 170), (193, 170), (194, 170), (195, 170), (196, 170), (197, 170), (198, 171), (199, 171), (200, 171), (201, 171), (202, 171), (203, 171), (204, 171), (205, 171), (206, 171), (207, 171), (208, 172), (209, 172), (210, 172), (211, 172), (212, 172), (213, 172), (214, 172), (215, 172), (216, 172), (217, 172), (218, 172), (219, 173), (220, 173), (221, 173), (222, 173), (223, 173), (224, 173), (225, 173), (226, 173), (227, 173), (228, 173), (229, 173), (230, 174), (231, 174), (232, 174), (233, 174), (234, 174), (235, 174), (236, 174), (237, 174), (238, 174), (239, 174), (240, 175), (241, 175), (242, 175), (243, 175), (244, 175), (245, 175), (245, 175), (246, 174), (247, 174), (248, 173), (249, 173), (250, 172), (251, 172), (252, 171), (253, 171), (254, 170), (255, 170), (256, 169), (257, 168), (258, 168), (259, 167), (260, 167), (261, 166), (262, 166), (263, 165), (264, 165), (265, 164), (266, 164), (267, 163), (268, 162), (269, 162), (270, 161), (271, 161), (272, 160), (273, 160), (274, 159), (275, 159), (276, 158), (277, 158), (278, 157), (279, 156), (280, 156), (281, 155), (282, 155), (283, 154), (284, 154), (285, 153), (286, 153), (287, 152), (288, 151), (289, 151), (290, 150), (291, 150), (292, 149), (293, 149), (294, 148), (295, 148), (296, 147), (297, 147), (298, 146), (299, 145), (300, 145), (301, 144), (302, 144), (303, 143), (304, 143), (305, 142), (306, 142), (307, 141), (308, 141), (309, 140), (309, 140), (310, 139), (311, 138), (312, 137), (313, 136), (314, 135), (315, 134), (316, 134), (317, 133), (318, 132), (319, 131), (320, 130), (321, 129), (322, 128), (322, 128), (323, 128), (324, 128), (325, 128), (326, 128), (326, 128), (327, 128), (327, 128), (327, 129)]
    points = []
    index = 取直线的最远一个坐标(points)
    print(index)

