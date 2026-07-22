"""
app/core/exceptions.py
======================
Custom exception hierarchy for Project Atlas.

Design rules:
- Every exception carries a machine-readable `error_code` for client parsing.
- HTTP status codes are set on the exception class, not at the call site.
- All exceptions inherit from AtlasBaseError so a single handler catches all.
- Never leak internal details (stack traces, SQL) in HTTP 4xx/5xx bodies.
"""

from __future__ import annotations

from typing import Any


class AtlasBaseError(Exception):
    """Root exception. All Project Atlas exceptions inherit from this."""

    http_status: int = 500
    error_code: str = "INTERNAL_ERROR"
    default_message: str = "An unexpected error occurred."

    def __init__(self, message: str | None = None, detail: Any = None) -> None:
        self.message = message or self.default_message
        self.detail = detail
        super().__init__(self.message)

    def to_dict(self) -> dict:
        payload: dict = {"error_code": self.error_code, "message": self.message}
        if self.detail is not None:
            payload["detail"] = self.detail
        return payload


# ── 400 Bad Request ───────────────────────────────────────────────────────────

class ValidationError(AtlasBaseError):
    http_status = 400
    error_code = "VALIDATION_ERROR"
    default_message = "Request validation failed."


class InvalidScenarioConfig(AtlasBaseError):
    http_status = 400
    error_code = "INVALID_SCENARIO_CONFIG"
    default_message = "Scenario configuration is invalid."


class SimulationParameterError(AtlasBaseError):
    http_status = 400
    error_code = "SIMULATION_PARAMETER_ERROR"
    default_message = "One or more simulation parameters are out of range."


# ── 401 Unauthorised ──────────────────────────────────────────────────────────

class AuthenticationError(AtlasBaseError):
    http_status = 401
    error_code = "AUTHENTICATION_FAILED"
    default_message = "Authentication credentials are missing or invalid."


class TokenExpiredError(AtlasBaseError):
    http_status = 401
    error_code = "TOKEN_EXPIRED"
    default_message = "Access token has expired. Please refresh your session."


class InvalidTokenError(AtlasBaseError):
    http_status = 401
    error_code = "INVALID_TOKEN"
    default_message = "The provided token is malformed or has an invalid signature."


# ── 403 Forbidden ─────────────────────────────────────────────────────────────

class PermissionDeniedError(AtlasBaseError):
    http_status = 403
    error_code = "PERMISSION_DENIED"
    default_message = "You do not have permission to perform this action."


class InsufficientRoleError(AtlasBaseError):
    http_status = 403
    error_code = "INSUFFICIENT_ROLE"
    default_message = "This action requires a higher privilege level."


# ── 404 Not Found ─────────────────────────────────────────────────────────────

class NotFoundError(AtlasBaseError):
    http_status = 404
    error_code = "NOT_FOUND"
    default_message = "The requested resource was not found."


class NodeNotFoundError(NotFoundError):
    error_code = "NODE_NOT_FOUND"
    default_message = "Supply chain node not found."


class LinkNotFoundError(NotFoundError):
    error_code = "LINK_NOT_FOUND"
    default_message = "Supply chain link not found."


class ScenarioNotFoundError(NotFoundError):
    error_code = "SCENARIO_NOT_FOUND"
    default_message = "Simulation scenario not found."


class SimulationRunNotFoundError(NotFoundError):
    error_code = "RUN_NOT_FOUND"
    default_message = "Simulation run not found."


# ── 409 Conflict ──────────────────────────────────────────────────────────────

class ConflictError(AtlasBaseError):
    http_status = 409
    error_code = "CONFLICT"
    default_message = "The request conflicts with the current state of the resource."


class SimulationAlreadyRunningError(ConflictError):
    error_code = "SIMULATION_ALREADY_RUNNING"
    default_message = "A simulation for this scenario is already running."


# ── 429 Rate Limited ──────────────────────────────────────────────────────────

class RateLimitExceededError(AtlasBaseError):
    http_status = 429
    error_code = "RATE_LIMIT_EXCEEDED"
    default_message = "Too many requests. Please wait before trying again."


# ── 500 Internal ──────────────────────────────────────────────────────────────

class DatabaseError(AtlasBaseError):
    http_status = 500
    error_code = "DATABASE_ERROR"
    default_message = "A database error occurred. Please try again."


class SimulationEngineError(AtlasBaseError):
    http_status = 500
    error_code = "SIMULATION_ENGINE_ERROR"
    default_message = "The simulation engine encountered an internal error."


class NetworkGraphError(AtlasBaseError):
    http_status = 500
    error_code = "NETWORK_GRAPH_ERROR"
    default_message = "Failed to construct or analyse the supply chain network graph."


class OptimizationError(AtlasBaseError):
    http_status = 500
    error_code = "OPTIMIZATION_ERROR"
    default_message = "The OR optimisation solver failed to find a feasible solution."
