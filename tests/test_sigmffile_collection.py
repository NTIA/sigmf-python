import tempfile
from sigmf.sigmffile_collection import SigMFFileCollection
from sigmf.sigmffile import fromarchive


def test_archive(test_sigmffile, test_alternate_sigmffile, test_alternate_sigmffile_2):
    input_sigmffile_collection = SigMFFileCollection(sigmffiles=[test_sigmffile, test_alternate_sigmffile])
    with tempfile.NamedTemporaryFile(suffix=".sigmf") as t_file:
        input_sigmffile_collection.archive(fileobj=t_file)
        output_sigmf_collection = fromarchive(archive_path=t_file.name)
        assert output_sigmf_collection.sigmffile_count() == 2
        assert output_sigmf_collection.get_sigmffiles() == [test_sigmffile, test_alternate_sigmffile]
