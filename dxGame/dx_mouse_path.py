


def get_mouse_path(current_x, current_y,target_x, target_y, min_n=10):
    trajectory = []


    dct = {
        550: 1,
        300: 2.1,
        200: 2.2,
        150: 2.3,
        100: 2.4,
        50: 2.55,
        25:2.58,
        0:2.6
    }
    step_v = 2
    while True:
        # 计算当前点到目标点的距离
        distance = ((target_x - current_x) ** 2 + (target_y - current_y) ** 2) ** 0.5
        # 检查是否到达目标
        if distance <= min_n:
            break
        for k, v in dct.items():

            # 根据距离决定移动步长
            if distance > k:  # 距离较远
                move_distance = distance / (v + step_v)  # 大步移动
                break
        else:
            move_distance = 1
        # 计算方向向量并进行移动
        direction_x = (target_x - current_x) / distance
        direction_y = (target_y - current_y) / distance

        # 更新当前位置
        step_x = round(direction_x * move_distance)
        step_y = round(direction_y * move_distance)

        current_x += step_x
        current_y += step_y

        # 添加当前位置到轨迹
        trajectory.append([step_x, step_y])  # 取整以模拟实际鼠标位置

    # 添加最终目的地
    trajectory.append((target_x-current_x, target_y-current_y))

    return trajectory

if __name__ == '__main__':

    # 示例用法
    target_x, target_y = -2000, 50
    mouse_path = get_mouse_path(0, 0, target_x, target_y)
    print(mouse_path)
