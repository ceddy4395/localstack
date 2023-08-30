# LocalStack Resource Provider Scaffolding v2
from __future__ import annotations

from pathlib import Path
from typing import Optional, Type, TypedDict

import localstack.services.cloudformation.provider_utils as util
from localstack.services.cloudformation.resource_provider import (
    CloudFormationResourceProviderPlugin,
    OperationStatus,
    ProgressEvent,
    ResourceProvider,
    ResourceRequest,
)


class IAMInstanceProfileProperties(TypedDict):
    Roles: Optional[list[str]]
    Arn: Optional[str]
    InstanceProfileName: Optional[str]
    Path: Optional[str]


REPEATED_INVOCATION = "repeated_invocation"


class IAMInstanceProfileProvider(ResourceProvider[IAMInstanceProfileProperties]):

    TYPE = "AWS::IAM::InstanceProfile"  # Autogenerated. Don't change
    SCHEMA = util.get_schema_path(Path(__file__))  # Autogenerated. Don't change

    def create(
        self,
        request: ResourceRequest[IAMInstanceProfileProperties],
    ) -> ProgressEvent[IAMInstanceProfileProperties]:
        """
        Create a new resource.

        Primary identifier fields:
          - /properties/InstanceProfileName

        Required properties:
          - Roles

        Create-only properties:
          - /properties/InstanceProfileName
          - /properties/Path

        Read-only properties:
          - /properties/Arn

        IAM permissions required:
          - iam:CreateInstanceProfile
          - iam:PassRole
          - iam:AddRoleToInstanceProfile
          - iam:GetInstanceProfile

        """
        model = request.desired_state
        iam = request.aws_client_factory.iam

        # defaults
        role_name = model.get("InstanceProfileName")
        if not role_name:
            role_name = util.generate_default_name(request.stack_name, request.logical_resource_id)
            model["InstanceProfileName"] = role_name

        response = iam.create_instance_profile(
            InstanceProfileName=model["InstanceProfileName"],
            Path=model["Path"],
        )
        for role_name in model.get("Roles", []):
            iam.add_role_to_instance_profile(
                InstanceProfileName=model["InstanceProfileName"], RoleName=role_name
            )
        model["Arn"] = response["InstanceProfile"]["Arn"]
        return ProgressEvent(
            status=OperationStatus.IN_PROGRESS,
            resource_model=model,
        )

    def read(
        self,
        request: ResourceRequest[IAMInstanceProfileProperties],
    ) -> ProgressEvent[IAMInstanceProfileProperties]:
        """
        Fetch resource information

        IAM permissions required:
          - iam:GetInstanceProfile
        """
        raise NotImplementedError

    def delete(
        self,
        request: ResourceRequest[IAMInstanceProfileProperties],
    ) -> ProgressEvent[IAMInstanceProfileProperties]:
        """
        Delete a resource

        IAM permissions required:
          - iam:GetInstanceProfile
          - iam:RemoveRoleFromInstanceProfile
          - iam:DeleteInstanceProfile
        """
        iam = request.aws_client_factory.iam
        instance_profile = iam.get_instance_profile(
            InstanceProfileName=request.previous_state["InstanceProfileName"]
        )
        for role in instance_profile["InstanceProfile"]["Roles"]:
            iam.remove_role_from_instance_profile(
                InstanceProfileName=request.previous_state["InstanceProfileName"],
                RoleName=role["RoleName"],
            )
        iam.delete_instance_profile(
            InstanceProfileName=request.previous_state["InstanceProfileName"]
        )
        return ProgressEvent(status=OperationStatus.IN_PROGRESS, resource_model={})

    def update(
        self,
        request: ResourceRequest[IAMInstanceProfileProperties],
    ) -> ProgressEvent[IAMInstanceProfileProperties]:
        """
        Update a resource

        IAM permissions required:
          - iam:PassRole
          - iam:RemoveRoleFromInstanceProfile
          - iam:AddRoleToInstanceProfile
          - iam:GetInstanceProfile
        """
        raise NotImplementedError


class IAMInstanceProfileProviderPlugin(CloudFormationResourceProviderPlugin):
    name = "AWS::IAM::InstanceProfile"

    def __init__(self):
        self.factory: Optional[Type[ResourceProvider]] = None

    def load(self):
        self.factory = IAMInstanceProfileProvider