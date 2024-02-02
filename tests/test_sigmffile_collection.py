import tempfile
from sigmf.sigmffile_collection import SigMFFileCollection
from sigmf.sigmffile import fromarchive


def test_archive(test_sigmffile, test_alternate_sigmffile, test_alternate_sigmffile_2):
    input_sigmffile_collection1 = SigMFFileCollection(sigmffiles=[test_sigmffile])
    with tempfile.NamedTemporaryFile(suffix=".sigmf") as t_file:
        input_sigmffile_collection1.archive(fileobj=t_file)
        output_sigmf_collection1 = fromarchive(archive_path=t_file.name)
        assert output_sigmf_collection1.sigmffile_count() == 1
        assert output_sigmf_collection1.get_sigmffiles() == [test_sigmffile]

    input_sigmffile_collection2 = SigMFFileCollection(sigmffiles=[test_sigmffile, test_alternate_sigmffile])
    with tempfile.NamedTemporaryFile(suffix=".sigmf") as t_file:
        input_sigmffile_collection2.archive(fileobj=t_file)
        output_sigmf_collection2 = fromarchive(archive_path=t_file.name)
        assert output_sigmf_collection2.sigmffile_count() == 2
        assert output_sigmf_collection2.get_sigmffiles() == [test_sigmffile, test_alternate_sigmffile]

    input_sigmffile_collection3 = SigMFFileCollection(sigmffiles=[test_sigmffile, test_alternate_sigmffile, test_alternate_sigmffile_2])
    with tempfile.NamedTemporaryFile(suffix=".sigmf") as t_file:
        input_sigmffile_collection3.archive(fileobj=t_file)
        output_sigmf_collection3 = fromarchive(archive_path=t_file.name)
        assert output_sigmf_collection3.sigmffile_count() == 3
        assert output_sigmf_collection3.get_sigmffiles() == [test_sigmffile, test_alternate_sigmffile, test_alternate_sigmffile_2]
