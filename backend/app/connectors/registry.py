from app.connectors.base import Connector


class ConnectorRegistry:
    def __init__(self) -> None:
        self._connectors: dict[
            str,
            Connector,
        ] = {}

    def register(
        self,
        connector: Connector,
    ) -> None:
        key = connector.key.strip()

        if not key:
            raise ValueError(
                "Connector key cannot be empty."
            )

        if key in self._connectors:
            raise ValueError(
                (
                    "Connector already registered: "
                    f"{key}"
                )
            )

        self._connectors[key] = connector

    def get(
        self,
        connector_key: str,
    ) -> Connector:
        connector = self._connectors.get(
            connector_key
        )

        if connector is None:
            raise ValueError(
                (
                    "Unknown connector: "
                    f"{connector_key}"
                )
            )

        return connector

    def resolve(
        self,
        *,
        connector_key: str,
        service: str,
    ) -> Connector:
        connector = self.get(
            connector_key
        )

        if not connector.supports_service(
            service
        ):
            raise ValueError(
                (
                    f"Connector '{connector_key}' "
                    "does not support service "
                    f"'{service}'."
                )
            )

        return connector

    def resolve_service(
        self,
        service: str,
    ) -> Connector:
        matches = [
            connector
            for connector
            in self._connectors.values()
            if connector.supports_service(
                service
            )
        ]

        if not matches:
            raise ValueError(
                (
                    "No connector supports "
                    f"service '{service}'."
                )
            )

        if len(matches) > 1:
            keys = sorted(
                connector.key
                for connector
                in matches
            )

            raise ValueError(
                (
                    "Multiple connectors support "
                    f"service '{service}': "
                    f"{', '.join(keys)}"
                )
            )

        return matches[0]

    def keys(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                self._connectors.keys()
            )
        )


connector_registry = ConnectorRegistry()