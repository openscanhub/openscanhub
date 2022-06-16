"""`covscanhub.scan` tests."""

from django.test import TestCase

from covscanhub.scan.compare import get_compare_title

CSS_CLASS_OTHER = "light_green_font"
CSS_CLASS_BASE = "red_font"


class CompareTestSuite(TestCase):
    def test1(self):
        result = get_compare_title(
            "libssh2-1.4.2-1.el6", "libssh2-1.2.2-7.el6"
        )
        self.assertEqual(
            result,
            (
                "libssh2-1."
                f'<span class="{CSS_CLASS_OTHER}">4</span>.'
                f'<span class="{CSS_CLASS_OTHER}">2</span>-'
                f'<span class="{CSS_CLASS_OTHER}">1</span>.'
                f'<span class="{CSS_CLASS_OTHER}">el6</span>'
                " compared to "
                "libssh2-1."
                f'<span class="{CSS_CLASS_BASE}">2</span>.'
                f'<span class="{CSS_CLASS_BASE}">2</span>-'
                f'<span class="{CSS_CLASS_BASE}">7</span>.'
                f'<span class="{CSS_CLASS_BASE}">el6</span>'
            )
        )

    def test2(self):
        result = get_compare_title("wget-1.12-1.8.el6", "wget-1.12-1.4.el6")
        self.assertEqual(
            result,
            (
                "wget-1.12-1."
                f'<span class="{CSS_CLASS_OTHER}">8</span>.'
                f'<span class="{CSS_CLASS_OTHER}">el6</span>'
                " compared to "
                "wget-1.12-1."
                f'<span class="{CSS_CLASS_BASE}">4</span>.'
                f'<span class="{CSS_CLASS_BASE}">el6</span>'
            )
        )

    def test3(self):
        result = get_compare_title(
            "btparser-0.17-1.el6", "btparser-0.16-3.el6"
        )
        self.assertEqual(
            result,
            (
                "btparser-0."
                f'<span class="{CSS_CLASS_OTHER}">17</span>-'
                f'<span class="{CSS_CLASS_OTHER}">1</span>.'
                f'<span class="{CSS_CLASS_OTHER}">el6</span>'
                " compared to "
                "btparser-0."
                f'<span class="{CSS_CLASS_BASE}">16</span>-'
                f'<span class="{CSS_CLASS_BASE}">3</span>.'
                f'<span class="{CSS_CLASS_BASE}">el6</span>'
            )
        )

    def test4(self):
        result = get_compare_title(
            "sysfsutils-2.1.0-7.el6", "sysfsutils-2.1.0-6.1.el6"
        )
        self.assertEqual(
            result,
            (
                "sysfsutils-2.1.0-"
                f'<span class="{CSS_CLASS_OTHER}">7</span>.'
                f'<span class="{CSS_CLASS_OTHER}">el6</span>'
                " compared to "
                "sysfsutils-2.1.0-"
                f'<span class="{CSS_CLASS_BASE}">6</span>.'
                f'<span class="{CSS_CLASS_BASE}">1</span>.'
                f'<span class="{CSS_CLASS_BASE}">el6</span>'
            )
        )

    def test5(self):
        result = get_compare_title("systemd-196-1.fc19", "systemd-191-2.fc18")
        self.assertEqual(
            result,
            (
                "systemd-"
                f'<span class="{CSS_CLASS_OTHER}">196</span>-'
                f'<span class="{CSS_CLASS_OTHER}">1</span>.'
                f'<span class="{CSS_CLASS_OTHER}">fc19</span>'
                " compared to "
                "systemd-"
                f'<span class="{CSS_CLASS_BASE}">191</span>-'
                f'<span class="{CSS_CLASS_BASE}">2</span>.'
                f'<span class="{CSS_CLASS_BASE}">fc18</span>'
            )
        )
