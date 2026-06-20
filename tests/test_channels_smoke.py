#!/usr/bin/env python3
"""Channel ACL smoke tests."""

import pytest
from werewolf_core.channels import ChannelAccessError, ChannelRegistry


def test_wolf_private_acl() -> None:
    channels = ChannelRegistry(wolves=["p1", "p6"], players=["p1", "p2", "p3", "p4", "p5", "p6"])

    wolf_channel = channels.get("wolf_private")
    wolf_channel.write(actor="p1", phase="night_werewolf", payload={"msg": "刀2"})

    # non-wolf cannot read
    with pytest.raises(ChannelAccessError):
        wolf_channel.read(actor="p2", phase="night_werewolf")

    # main cannot read wolf channel
    with pytest.raises(ChannelAccessError):
        wolf_channel.read(actor="main", phase="night_werewolf")
