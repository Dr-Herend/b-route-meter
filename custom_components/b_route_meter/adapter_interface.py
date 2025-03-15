"""Define the adapter interface for B-route communication."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional

# BP35A1命令参考：
# SKINFO: 获取基本信息
#   - MAC地址（64位）
#   - IPv6地址
#   - 当前使用的信道
#   - PAN ID
# SKVER: 获取SKSTACK IP固件版本
# SKAPPVER: 获取应用程序固件版本
# SKTABLE: 获取网络状态
#   - E: 显示UDP/TCP端口状态
#   - F: 显示TCP连接状态
#   - 1: 显示可用的IP地址列表
#   - 2: 显示邻居缓存


@dataclass
class DiagnosticInfo:
    """Data class for device diagnostic information."""

    # Device identity
    mac_address: Optional[str] = None  # 64-bit MAC address
    ipv6_address: Optional[str] = None  # Link local IPv6 address

    # Version information
    stack_version: Optional[str] = None  # SKSTACK IP firmware version
    app_version: Optional[str] = None  # Application firmware version

    # Network configuration
    channel: Optional[int] = None  # Current channel number
    pan_id: Optional[str] = None  # Current PAN ID

    # Network status
    active_tcp_connections: List[
        Dict[str, str]
    ] = None  # List of active TCP connections
    udp_ports: List[int] = None  # List of UDP ports in use
    tcp_ports: List[int] = None  # List of TCP ports in use
    neighbor_devices: List[Dict[str, str]] = None  # List of neighbor devices


@dataclass
class MeterReading:
    """Data class for meter readings."""

    power: Optional[float] = None  # W
    current: Optional[float] = None  # A
    voltage: Optional[float] = None  # V
    forward: Optional[float] = None  # kWh
    reverse: Optional[float] = None  # kWh
    forward_timestamp: Optional[str] = None
    reverse_timestamp: Optional[str] = None


class AdapterInterface(ABC):
    """Abstract interface for B-route adapters."""

    """Abstract interface for B-route adapters."""

    @abstractmethod
    def connect(self) -> None:
        """Establish connection with the smart meter."""
        pass

    @abstractmethod
    def get_data(self) -> MeterReading:
        """Read data from the smart meter.

        Returns:
            MeterReading: The latest meter readings
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the connection with the smart meter."""
        pass

    @abstractmethod
    def get_diagnostic_info(self) -> DiagnosticInfo:
        """Get diagnostic information from the device.

        Returns:
            DiagnosticInfo: Device diagnostic information including network status
        """
        pass
