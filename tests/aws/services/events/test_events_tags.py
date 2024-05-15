import json

import pytest

from localstack.testing.pytest import markers
from localstack.utils.strings import short_uid
from tests.aws.services.events.test_events import TEST_EVENT_PATTERN


@markers.aws.validated
@pytest.mark.parametrize("resource_to_tag", ["event_bus", "rule"])
def tests_tag_untag_resource(
    resource_to_tag,
    events_create_event_bus,
    events_put_rule,
    aws_client,
    snapshot,
):
    bus_name = f"test_bus-{short_uid()}"
    response = events_create_event_bus(Name=bus_name)
    event_bus_arn = response["EventBusArn"]

    rule_name = f"test_rule-{short_uid()}"
    response = events_put_rule(
        Name=rule_name,
        EventBusName=bus_name,
        EventPattern=json.dumps(TEST_EVENT_PATTERN),
    )
    rule_arn = response["RuleArn"]

    if resource_to_tag == "event_bus":
        resource_arn = event_bus_arn
    if resource_to_tag == "rule":
        resource_arn = rule_arn
    tag_key_2 = "tag2"
    response_tag_resource = aws_client.events.tag_resource(
        ResourceARN=resource_arn,
        Tags=[
            {
                "Key": "tag1",
                "Value": "value1",
            },
            {
                "Key": tag_key_2,
                "Value": "value2",
            },
        ],
    )
    snapshot.match("tag_resource", response_tag_resource)

    response = aws_client.events.list_tags_for_resource(ResourceARN=resource_arn)
    snapshot.match("list_tags_for_resource", response)

    response_untag_resource = aws_client.events.untag_resource(
        ResourceARN=resource_arn,
        TagKeys=[tag_key_2],
    )
    snapshot.match("untag_resource", response_untag_resource)

    response = aws_client.events.list_tags_for_resource(ResourceARN=resource_arn)
    snapshot.match("list_tags_for_untagged_resource", response)


@markers.aws.validated
@pytest.mark.parametrize("resource_to_tag", ["not_existing_rule", "not_existing_event_bus"])
def tests_tag_list_untag_not_existing_resource(
    resource_to_tag,
    region_name,
    account_id,
    aws_client,
    snapshot,
):
    resource_name = short_uid()
    if resource_to_tag == "not_existing_rule":
        resource_arn = f"arn:aws:events:{region_name}:{account_id}:rule/{resource_name}"
    if resource_to_tag == "not_existing_event_bus":
        resource_arn = f"arn:aws:events:{region_name}:{account_id}:event-bus/{resource_name}"

    tag_key_1 = "tag1"
    with pytest.raises(aws_client.events.exceptions.ResourceNotFoundException) as error:
        aws_client.events.tag_resource(
            ResourceARN=resource_arn,
            Tags=[
                {
                    "Key": tag_key_1,
                    "Value": "value1",
                },
            ],
        )

    snapshot.match("tag_not_existing_resource_error", error)

    snapshot.add_transformer(snapshot.transform.regex(resource_name, "<not-existing-resource-name>"))
    with pytest.raises(aws_client.events.exceptions.ResourceNotFoundException) as error:
        aws_client.events.list_tags_for_resource(ResourceARN=resource_arn)
    snapshot.match("list_tags_for_not_existing_resource_error", error)

    with pytest.raises(aws_client.events.exceptions.ResourceNotFoundException) as error:
        aws_client.events.untag_resource(
            ResourceARN=resource_arn,
            TagKeys=[tag_key_1],
        )
    snapshot.match("untag_not_existing_resource_error", error)


class TestRuleTags:
    @markers.aws.validated
    def test_put_rule_with_tags(
        self, events_create_event_bus, events_put_rule, aws_client, snapshot
    ):
        bus_name = f"test_bus-{short_uid()}"
        events_create_event_bus(Name=bus_name)

        rule_name = f"test_rule-{short_uid()}"
        response_put_rule = events_put_rule(
            Name=rule_name,
            EventPattern=json.dumps(TEST_EVENT_PATTERN),
            Tags=[
                {
                    "Key": "tag1",
                    "Value": "value1",
                },
                {
                    "Key": "tag2",
                    "Value": "value2",
                },
            ],
        )
        rule_arn = response_put_rule["RuleArn"]
        snapshot.match("put_rule_with_tags", response_put_rule)

        response_put_rule = aws_client.events.list_tags_for_resource(ResourceARN=rule_arn)
        snapshot.add_transformer(snapshot.transform.regex(rule_name, "<rule_name>"))
        snapshot.match("list_tags_for_rule", response_put_rule)


class TestEventBusTags:
    @markers.aws.validated
    def test_create_event_bus_with_tags(self, events_create_event_bus, aws_client, snapshot):
        bus_name = f"test_bus-{short_uid()}"
        response_create_event_bus = events_create_event_bus(
            Name=bus_name,
            Tags=[
                {
                    "Key": "tag1",
                    "Value": "value1",
                },
                {
                    "Key": "tag2",
                    "Value": "value2",
                },
            ],
        )
        bus_arn = response_create_event_bus["EventBusArn"]
        snapshot.match("create_event_bus_with_tags", response_create_event_bus)

        response_create_event_bus = aws_client.events.list_tags_for_resource(ResourceARN=bus_arn)
        snapshot.add_transformer(snapshot.transform.regex(bus_name, "<bus_name>"))
        snapshot.match("list_tags_for_event_bus", response_create_event_bus)