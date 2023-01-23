# -*- coding: utf-8 -*-

from osh.hub.other.decorators import public


@public
def remove_duplicities(analyzers):
    def get_latest_analyzer(an_name):
        for a in reversed(analyzers):
            if a.startswith(an_name + '-'):
                return a
    final_list = []
    for analyzer in analyzers:
        try:
            an_name = analyzer.split('-')[0]
        except KeyError:
            final_list.append(analyzer)
            continue
        last_an = get_latest_analyzer(an_name)
        if last_an not in final_list:
            if last_an is None:
                final_list.append(analyzer)
            else:
                final_list.append(last_an)
    return final_list


def test():
    assert remove_duplicities(['a', 'b']) == ['a', 'b']
    assert remove_duplicities(['a-c', 'a-d', 'b']) == ['a-d', 'b']
    assert remove_duplicities(['a-c', 'a-d', 'b-a', 'b-d']) == ['a-d', 'b-d']


if __name__ == '__main__':
    test()
