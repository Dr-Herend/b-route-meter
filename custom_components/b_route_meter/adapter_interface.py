"""Define the adapter interface for B-route communication."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional

# BP35A1 Command Reference:
# SKINFO: Get basic information
#   - MAC address (64-bit)
#   - IPv6 address
#   - Current channel in use
#   - PAN ID
# SKVER: Get SKSTACK IP firmware version
# SKAPPVER: Get application firmware version
# SKTABLE: Get network status
#   - E: Show UDP/TCP port status
#   - F: Show TCP connection status
#   - 1: Show available IP address list
#   - 2: Show neighbor cache


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
    rssi: Optional[int] = None  # Received Signal Strength Indicator (dBm)

    # Network status
    active_tcp_connections: Optional[List[Dict[str, str]]] = (
        None  # List of active TCP connections
    )
    udp_ports: Optional[List[int]] = None  # List of UDP ports in use
    tcp_ports: Optional[List[int]] = None  # List of TCP ports in use
    neighbor_devices: Optional[List[Dict[str, str]]] = None  # List of neighbor devices


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

    # Phase current values
    r_phase_current: Optional[float] = None  # R-phase current (A)
    t_phase_current: Optional[float] = None  # T-phase current (A)

    # Additional ECHONET Lite attributes
    operation_status: Optional[bool] = None  # 0x80 - Operation status (ON/OFF)
    error_status: Optional[bool] = None  # 0x82 - Error status (Normal/Error)
    current_limit: Optional[float] = None  # 0x97 - Current limit capacity (A)
    meter_type: Optional[str] = None  # 0x98 - Meter classification
    detected_abnormality: Optional[str] = None  # 0xD3 - Detected abnormality
    power_unit: Optional[float] = (
        None  # 0xD7 - Cumulative effective power unit (usually 0.1kWh)
    )

    # If any supported attribute has a value, mark this meter as supporting this feature
    has_operational_info: Optional[bool] = (
        False  # Whether operation status info is supported
    )
    has_limit_info: Optional[bool] = False  # Whether limit info is supported
    has_abnormality_detection: Optional[bool] = (
        False  # Whether abnormality detection is supported
    )


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
