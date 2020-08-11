# type: ignore

from datetime import datetime
import uuid

import simplejson as json

from chaosiqagent.json import JSONEncoder


def test_can_encode_uuid_into_json():
    uid = uuid.uuid4()
    encoded = json.dumps({"user_id": uid}, cls=JSONEncoder, indent=0)
    assert encoded == '{\n"user_id": "'+str(uid)+'"\n}'


def test_can_encode_datetime_into_json():
    now = datetime.now()
    encoded = json.dumps({"now": now}, cls=JSONEncoder, indent=0)
    assert encoded == '{\n"now": "'+now.isoformat()+'"\n}'
