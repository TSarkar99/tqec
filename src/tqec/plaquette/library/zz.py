import cirq

from tqec.detectors.gate import DetectorGate, RelativeMeasurement
from tqec.enums import PlaquetteOrientation
from tqec.plaquette.plaquette import PlaquetteList, RoundedPlaquette
from tqec.plaquette.schedule import ScheduledCircuit
from tqec.position import Shape2D


class BaseZZPlaquette(RoundedPlaquette):
    def __init__(
        self, circuit: ScheduledCircuit, orientation: PlaquetteOrientation
    ) -> None:
        super().__init__(circuit, orientation)

    @property
    def shape(self) -> Shape2D:
        # Hack to check the pre-condition that all Plaquette instances should
        # have the same shape.
        return Shape2D(3, 3)


class ZZInitialisationPlaquette(BaseZZPlaquette):
    def __init__(
        self,
        orientation: PlaquetteOrientation,
        schedule: list[int],
        include_detector: bool = True,
    ):
        (syndrome_qubit,) = [
            q.to_grid_qubit() for q in RoundedPlaquette.get_syndrome_qubits()
        ]
        data_qubits = [
            q.to_grid_qubit() for q in RoundedPlaquette.get_data_qubits(orientation)
        ]
        detector = []
        if include_detector:
            detector = [
                DetectorGate(
                    syndrome_qubit,
                    [RelativeMeasurement(cirq.GridQubit(0, 0), -1)],
                    time_coordinate=0,
                ).on(syndrome_qubit),
            ]
        super().__init__(
            circuit=ScheduledCircuit(
                cirq.Circuit(
                    [
                        [
                            cirq.R(q).with_tags(self._MERGEABLE_TAG)
                            for q in [syndrome_qubit, *data_qubits]
                        ],
                        [cirq.CX(data_qubits[0], syndrome_qubit)],
                        [cirq.CX(data_qubits[1], syndrome_qubit)],
                        [cirq.M(syndrome_qubit)],
                        detector,
                    ]
                ),
                schedule,
            ),
            orientation=orientation,
        )


class ZZMemoryPlaquette(BaseZZPlaquette):
    def __init__(
        self,
        orientation: PlaquetteOrientation,
        schedule: list[int],
        include_detector: bool = True,
    ):
        (syndrome_qubit,) = [
            q.to_grid_qubit() for q in RoundedPlaquette.get_syndrome_qubits()
        ]
        data_qubits = [
            q.to_grid_qubit() for q in RoundedPlaquette.get_data_qubits(orientation)
        ]
        detector = [
            DetectorGate(
                syndrome_qubit,
                [
                    RelativeMeasurement(cirq.GridQubit(0, 0), -1),
                    RelativeMeasurement(cirq.GridQubit(0, 0), -2),
                ],
                time_coordinate=0,
            ).on(syndrome_qubit),
        ]
        super().__init__(
            circuit=ScheduledCircuit(
                cirq.Circuit(
                    [
                        [
                            cirq.R(q).with_tags(self._MERGEABLE_TAG)
                            for q in [syndrome_qubit]
                        ],
                        [cirq.CX(data_qubits[0], syndrome_qubit)],
                        [cirq.CX(data_qubits[1], syndrome_qubit)],
                        [cirq.M(syndrome_qubit)],
                        detector,
                    ]
                ),
                schedule,
            ),
            orientation=orientation,
        )


class ZZFinalMeasurementPlaquette(BaseZZPlaquette):
    def __init__(
        self,
        orientation: PlaquetteOrientation,
        include_detector: bool = True,
    ):
        (syndrome_qubit,) = [
            q.to_grid_qubit() for q in RoundedPlaquette.get_syndrome_qubits()
        ]
        data_qubits = [
            q.to_grid_qubit() for q in RoundedPlaquette.get_data_qubits(orientation)
        ]
        detector = [
            cirq.Moment(
                DetectorGate(
                    syndrome_qubit,
                    [
                        RelativeMeasurement(cirq.GridQubit(0, 0), -1),
                        *[
                            RelativeMeasurement(dq - syndrome_qubit, -1)
                            for dq in data_qubits
                        ],
                    ],
                    time_coordinate=1,
                ).on(syndrome_qubit)
            )
        ]
        super().__init__(
            circuit=ScheduledCircuit(
                cirq.Circuit(
                    [
                        cirq.Moment(
                            [
                                cirq.M(q).with_tags(self._MERGEABLE_TAG)
                                for q in data_qubits
                            ]
                        ),
                    ]
                    + (detector if include_detector else [])
                ),
            ),
            orientation=orientation,
        )


class ZZPlaquetteList(PlaquetteList):
    def __init__(
        self,
        orientation: PlaquetteOrientation,
        schedule: list[int],
        include_detector: bool = True,
    ):
        super().__init__(
            [
                ZZInitialisationPlaquette(orientation, schedule, include_detector),
                ZZMemoryPlaquette(orientation, schedule),
                ZZFinalMeasurementPlaquette(orientation, include_detector),
            ]
        )
