"""
core/middleware/admin_debug.py
-------------------------------
Middleware that catches exceptions on /admin and shows a detailed
traceback in the browser response (dev only).
"""

import traceback
import sys

from django.http import HttpResponse


class AdminDebugMiddleware:
    """
    Catch any exceptions on /admin and print the exact traceback to
    both the console AND the browser response body.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if not request.path.startswith('/admin'):
            return None

        exc_type, exc_value, exc_tb = sys.exc_info()
        tb_string = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))

        print("================ ADMIN CRASH ==================", file=sys.stderr)
        print(tb_string, file=sys.stderr)
        print("===============================================", file=sys.stderr)

        safe_tb = tb_string.replace("`", "\\`").replace("$", "\\$")
        return HttpResponse(
            f"""
            <html>
            <body style="font-family: monospace; padding: 20px;">
                <h2>Admin Page Crashed</h2>
                <p style="color: red;">Check your Browser Console (F12) for the exact Python error!</p>
                <script>
                    console.error(`===== PYTHON SERVER CRASH =====\\n\\n${{safe_tb}}`)
                </script>
                <hr>
                <pre>{tb_string}</pre>
            </body>
            </html>
            """,
            status=500,
        )
