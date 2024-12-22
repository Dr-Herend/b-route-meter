# B-Route 智能电表 Home Assistant 集成组件

这是一个用于 Home Assistant 的自定义集成组件,可以通过 B-route 接口读取日本智能电表的数据。

## 功能特点

- 支持通过 B-route 接口读取以下数据:
  - 瞬时功率 (E7)
  - 瞬时电流 (E8)
  - 瞬时电压 (E9)
  - 正向累计用电量 (EA)
  - 反向累计用电量 (EB)
- 自动进行信道扫描和 PANA 认证
- 每10秒自动更新数据
- 支持通过 Home Assistant UI 配置

## 安装要求

- Home Assistant 2023.x 或更高版本
- 支持 B-route 的智能电表
- B-route 认证 ID 和密码
- USB 转 Wi-SUN 适配器

## 安装方法

1. 将 `b_route_meter` 文件夹复制到 Home Assistant 的 `custom_components` 目录下
2. 重启 Home Assistant
3. 在集成页面中添加 "B-Route Smart Meter" 集成
4. 输入以下配置信息:
   - B-route ID (从电力公司获取)
   - B-route 密码
   - 串口设备路径 (默认: /dev/ttyS0)

## 配置参数

| 参数 | 说明 | 必填 | 默认值 |
|------|------|------|--------|
| route_b_id | B-route ID | 是 | - |
| route_b_pwd | B-route 密码 | 是 | - |
| serial_port | 串口设备路径 | 否 | /dev/ttyS0 |

## 传感器实体

安装后会创建以下传感器实体:

- `sensor.b_route_instantaneous_power`: 瞬时功率 (W)
- `sensor.b_route_instantaneous_current`: 瞬时电流 (A)
- `sensor.b_route_instantaneous_voltage`: 瞬时电压 (V)
- `sensor.b_route_cumulative_forward`: 正向累计用电量 (kWh)
- `sensor.b_route_cumulative_reverse`: 反向累计用电量 (kWh)

## 故障排除

如果遇到连接问题:

1. 确认 B-route ID 和密码是否正确
2. 检查串口设备路径是否正确
3. 确认智能电表是否支持 B-route 功能
4. 查看 Home Assistant 日志中的详细错误信息

## 参考资料

- [B ルート ID 申请 (TEPCO)](https://www.tepco.co.jp/pg/consignment/liberalization/smartmeter-broute.html)
- [ECHONET Lite 规格书](https://echonet.jp/spec_g/)

