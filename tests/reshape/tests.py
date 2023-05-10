import pytest

from socon.utils.reshape import TemplateEngine


@pytest.fixture()
def example(datafix_dir) -> TemplateEngine:
    reshape_file = TemplateEngine(datafix_dir / "example.txt")
    yield reshape_file
    reshape_file.revert_modif()


class TemplateEngineTests:
    def test_read_file(self, example, capsys):
        """Read the content of the file that need to be reshape"""
        example.read_file()
        captured = capsys.readouterr()
        with open(example.file, "r") as f:
            content = f.read()
        assert content == captured.out

    def test_render_template(self, example, datafix_dir):
        """Check if we are well rendering a template with a variable"""
        template = TemplateEngine(datafix_dir / "template.txt")
        example.render({"foo": "I'm foo variable"})
        assert example == template

    def test_revert_modification(self, example):
        """Revert the modification applied"""
        content = example.content
        example.replace("# We can replace.*", "I'm replacing a line")
        example.revert_modif()
        assert example.content == content

    def test_reshape_file(self, example, datafix_dir):
        """
        Use the reshape method to apply all modification to the current file
        """
        template = TemplateEngine(datafix_dir / "template.txt")
        example.render({"foo": "I'm foo variable"})
        example.reshape()
        assert example == template

    def test_write_content_to_file(self, test_dir, example):
        """Write the content to a file to another destination"""
        example.render({"foo": "I'm foo variable"})
        output_file = test_dir / "output.txt"
        example.write(dest=output_file)
        with open(str(output_file), "r") as f:
            content = f.read()
        assert content == example.content
