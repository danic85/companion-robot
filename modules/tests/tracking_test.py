from unittest import mock, TestCase
from modules.coral.tracking import Tracking

@mock.patch('modules.coral.tracking.pub', return_value=mock.Mock())
class TrackingTest(TestCase):
    def test_calc_move_amount_pan(self, mock_pub):
        mock_pub.sendMessage.reset_mock()
        quarter_screen = Tracking.VIDEO_SIZE[0]/4
        val = Tracking.calc_move_amount_pan(quarter_screen, quarter_screen*2)
        assert val == 0

        val = Tracking.calc_move_amount_pan(quarter_screen, quarter_screen)
        assert val == 11

        val = Tracking.calc_move_amount_pan(Tracking.VIDEO_SIZE[0]/2, quarter_screen)
        assert val == -11

        val = Tracking.calc_move_amount_pan(0, quarter_screen)
        assert val == 33