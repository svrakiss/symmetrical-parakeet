import factory
from photoAlbum import album
from pandas.util.testing import assert_frame_equal
def test_rename():
    new_dict = {'tr':33434,'ttt':55,'expected':45}
    output_dict = factory.rename('test',new_dict)
    assert output_dict.get('test 1') == new_dict['tr']
    assert output_dict.get('test 2') == new_dict['ttt']
    assert output_dict.get('test 3') == new_dict['expected']

def test_rename_albums():
    filename = "deluxe test.xlsx"
    output_dict=factory.build_with_dict("Deluxe Elimination Round",filename=filename)
    old_dict = album(filename)
    assert_frame_equal(output_dict.albumDict.get("Deluxe Elimination Round 1") ,old_dict.albumDict.get("None 1"))
    assert_frame_equal(output_dict.albumDict.get("Deluxe Elimination Round 2") ,old_dict.albumDict.get("None 2"))
