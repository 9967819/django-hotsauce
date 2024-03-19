import os

MOUNTPOINTS = {
    'test' : dict(
        root=os.path.realpath(\
            os.path.join(\
                os.path.dirname(__file__), 'data')
                )
    ),
    'bob' : dict(
        root='/home/bob',
        username='bob',
        password='secret'
        )
}

# Use these settings, if config file does not define them (or is totally missing)
DEFAULT_CONFIG = {
    "mount_path": None,  # Application root, e.g. <mount_path>/<share_name>/<res_path>               
    "provider_mapping": {},
    "host": "localhost",
    "port": 8080, 
    "ext_servers": ["wsgiref", "cherrypy-bundled", "wsgidav"],
    "enable_loggers": [],
    "propsmanager": None,  # True: use property_manager.PropertyManager                  
    "locksmanager": True,  # True: use lock_manager.LockManager    
    
    # HTTP Authentication Options
    "user_mapping": {},       # dictionary of dictionaries 
    "domaincontroller": None, # None: domain_controller.WsgiDAVDomainController(user_mapping)
    "acceptbasic": True,      # Allow basic authentication, True or False
    "acceptdigest": True,     # Allow digest authentication, True or False
    "defaultdigest": True,    # True (default digest) or False (default basic)
    
    # Verbose Output
    "verbose": 3,       # 0 - no output (excepting application exceptions)         
                        # 1 - show single line request summaries (for HTTP logging)
                        # 2 - show additional events
                        # 3 - show full request/response header info (HTTP Logging)
                        #     request body and GET response bodies not shown
    
    "dir_browser": {
        "enable": True,          # Render HTML listing for GET requests on collections
        "response_trailer": "",  # Raw HTML code, appended as footer
        "davmount": False,       # Send <dm:mount> response if request URL contains '?davmount'
        "msmount": False,        # Add an 'open as webfolder' link (requires Windows)
    }
}

