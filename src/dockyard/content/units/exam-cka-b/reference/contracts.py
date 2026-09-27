import subprocess,yaml
role={'apiVersion':'rbac.authorization.k8s.io/v1','kind':'Role','metadata':{'name':'release-operator','namespace':'dispatch'},'rules':[{'apiGroups':['apps'],'resources':['deployments'],'verbs':['get','list']},{'apiGroups':['apps'],'resources':['deployments/scale'],'verbs':['get','patch','update']}]}
binding={'apiVersion':'rbac.authorization.k8s.io/v1','kind':'RoleBinding','metadata':{'name':'release-operator','namespace':'dispatch'},'subjects':[{'kind':'ServiceAccount','name':'release-operator','namespace':'dispatch'}],'roleRef':{'apiGroup':'rbac.authorization.k8s.io','kind':'Role','name':'release-operator'}}
budget={'apiVersion':'policy/v1','kind':'PodDisruptionBudget','metadata':{'name':'dispatch-maintenance','namespace':'dispatch'},'spec':{'minAvailable':1,'selector':{'matchLabels':{'app':'dispatch','track':'stable'}}}}
subprocess.run(['kubectl','apply','-f','-'],input=yaml.safe_dump_all([role,binding,budget]),text=True,check=True)
