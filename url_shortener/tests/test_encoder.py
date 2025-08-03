import pytest

from url_shortener.encoder import Base62Encoder


def test_encode_negative_number(encoder: Base62Encoder):
    with pytest.raises(
        ValueError, match="Base62 encoding does not support negative numbers."
    ):
        encoder.encode(-1)


@pytest.mark.parametrize(
    "first_number,second_number,are_same",
    (
        [1, 1, True],
        [1, 1000, False],
        [1000, 1, False],
        [1000, 1000, True],
    ),
)
def test_same_input_same_output(
    first_number: int,
    second_number: int,
    are_same: bool,
    encoder: Base62Encoder,
):
    assert (encoder.encode(first_number) == encoder.encode(second_number)) == are_same
