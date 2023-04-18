def stat_function(order, group, short_comment, comment):
    def decorator(function):
        function.order = order
        function.group = group
        function.short_comment = short_comment
        function.comment = comment
        return function
    return decorator
