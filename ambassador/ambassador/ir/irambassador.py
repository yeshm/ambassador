from typing import Dict, Optional, TYPE_CHECKING

from ..config import Config

from .irresource import IRResource
from .irtls import IREnvoyTLS

if TYPE_CHECKING:
    from .ir import IR


class IRAmbassador (IRResource):
    service_port: int

    def __init__(self, ir: 'IR', aconf: Config,
                 rkey: str="ir.auth",
                 kind: str="IRAuth",
                 name: str="ir.auth",
                 **kwargs) -> None:
        print("IRAmbassador __init__ (%s %s %s)" % (kind, name, kwargs))

        super().__init__(
            ir=ir, aconf=aconf, rkey=rkey, kind=kind, name=name,
            service_port=80,
            admin_port=8001,
            diag_port=8877,
            auth_enabled=None,
            liveness_probe={"enabled": True},
            readiness_probe={"enabled": True},
            diagnostics={"enabled": True},
            use_proxy_proto=False,
            x_forwarded_proto_redirect=False,
            **kwargs
        )

    def setup(self, ir: 'IR', aconf: Config) -> bool:
        # We're interested in the 'ambassador' module from the Config, if any...
        amod = aconf.get_module("ambassador")

        # Is there a TLS module in the Ambassador module?
        tmod: Optional[Dict] = None

        if amod:
            tmod = amod.get('tls', None)
            self.referenced_by(amod)

        if tmod:
            # Yes. Get its contexts loaded.
            for ctx_name in tmod.keys():
                if ctx_name.startswith('_'):
                    continue

                IREnvoyTLS(ir=ir, aconf=aconf, name=ctx_name, **tmod[ctx_name ])

        # Next up, check for the special 'server' and 'client' TLS contexts.
        ctx = ir.get_tls_context('server')

        if ctx:
            # Server-side TLS is enabled; switch to port 443.
            self.logger.debug("TLS termination enabled!")
            self.service_port = 443

        ctx = ir.get_tls_context('client')

        if ctx:
            # Client-side TLS is enabled.
            self.logger.debug("TLS client certs enabled!")

        # After that, check for port definitions, probes, etc., and copy them in
        # as we find them.
        for key in [ 'service_port', 'admin_port', 'diag_port',
                     'liveness_probe', 'readiness_probe', 'auth_enabled',
                     'use_proxy_proto', 'use_remote_address', 'diagnostics', 'x_forwarded_proto_redirect' ]:
            if amod and (key in amod):
                # Yes. It overrides the default.
                self[key] = amod[key]

        return True