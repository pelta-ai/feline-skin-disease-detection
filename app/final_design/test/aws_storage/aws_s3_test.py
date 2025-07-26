import unittest
import boto3
from moto import mock_aws
from datetime import date
import os
import tempfile
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from lib.aws_storage import aws_s3 as s3_module
from lib.aws_storage import aws_s3_constants as constants

@mock_aws
class Aws_S3_Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        s3_module.s3_client = constants.S3_CLIENT_EMULATOR
        s3_module.s3_client.create_bucket(Bucket='felineskindiseasedetectionbucket')

    def test_folder_exists_true(self):
        path = 'testuser/folder2/'
        s3_module._create_folder_helper(path)
        self.assertTrue(s3_module.folder_exists(path))

    def test_folder_exists_false(self):
        self.assertFalse(s3_module.folder_exists('nonexistentuser/folder/'))

    def test_create_user_folder(self):
        user_id = 'userfolder1'
        s3_module.create_user_folder(user_id)
        objects = s3_module.list_objects(prefix=user_id)
        self.assertTrue(any(user_id in obj['Key'] for obj in objects))

    def test_create_today_folder(self):
        user_id = 'user123'
        s3_module.create_today_folder(user_id)
        today = s3_module._get_today_date()
        keys = [obj['Key'] for obj in s3_module.list_objects(prefix=user_id)]
        self.assertIn(f"{user_id}/{today}/images/", keys)
        self.assertIn(f"{user_id}/{today}/diagnosis/", keys)

    def test_add_file_image(self):
        user_id = 'imageuser'
        today = s3_module._get_today_date()
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp:
            temp.write(b'test image')
            temp.flush()
            s3_module.add_file(os.path.basename(temp.name), temp.name, user_id)
            objects = s3_module.list_objects(prefix=user_id)
            self.assertTrue(any(today in obj['Key'] for obj in objects))
        os.unlink(temp.name)

    def test_add_file_txt(self):
        user_id = 'txtuser'
        today = s3_module._get_today_date()
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp:
            temp.write(b'diagnosis result')
            temp.flush()
            s3_module.add_file(os.path.basename(temp.name), temp.name, user_id)
            objects = s3_module.list_objects(prefix=user_id)
            self.assertTrue(any(today in obj['Key'] for obj in objects))
        os.unlink(temp.name)

    def test_get_file_url_success(self):
        user_id = 'urluser'
        today = s3_module._get_today_date()
        file_key = f"{user_id}/{today}/images/test.jpg"
        s3_module._create_folder_helper(f"{user_id}/{today}/images/")
        s3_module.s3_client.put_object(Bucket=constants.BUCKET, Key=file_key, Body=b'data')
        url = s3_module.get_file_url(file_key)
        self.assertTrue(url.startswith("http"))


if __name__ == '__main__':
    unittest.main()