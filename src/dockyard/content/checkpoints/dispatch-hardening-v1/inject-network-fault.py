import json,subprocess
patch={"spec":{"ingress":[{"from":[{"namespaceSelector":{"matchLabels":{"kubernetes.io/metadata.name":"frontend"}},"podSelector":{"matchLabels":{"app":"retired-client"}}}],"ports":[{"protocol":"TCP","port":8080}]}]}}
subprocess.run(["kubectl","patch","networkpolicy","allow-business-reads","--type=merge","-p",json.dumps(patch)],check=True)
