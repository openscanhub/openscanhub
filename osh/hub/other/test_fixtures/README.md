## Fixtures howto

The fixtures in this directory need to be loaded manually in case needed.

- `users.json`

    - Fixture generation

        The `users.json` fixture is generated via:
        ```
        podman exec osh-hub python3 osh/hub/manage.py dumpdata --indent 2 kobo_auth.User > osh/hub/other/test_fixtures/users.json
        ```

    - Initial users

        The `users.json` fixture consists of following users:

        username | password | is_superuser |
        ---------|----------|--------------|
        admin    | xxxxxx   | True
        user     | xxxxxx   | False

        The initial fixture was based on the original account setup in `init-db.sh`. If you need to customize, either open a django shell or update from the admin panel. If you want your local changes to be persisted, feel free to update the fixtures directly.
