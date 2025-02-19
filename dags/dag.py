from airflow.decorators import dag, task
import subprocess
from airflow.models import DagBag
from datetime import datetime
import logging
import json
import yaml

default_args = {"owner": "data-team"}


@dag(
    dag_id="manage_airflow_roles",
    default_args=default_args,
    start_date=datetime(2025, 2, 14),
    schedule_interval="0 10 * * 1",
    catchup=False,
)
def manage_airflow_roles():
    @task()
    def list_roles() -> list:
        """
        List all roles in Airflow
        Returns:
            list: List of roles
        """
        result = subprocess.run(
            ["airflow", "roles", "list", "-o", "json"], capture_output=True, text=True
        )

        roles = json.loads(result.stdout)
        dag_roles = []

        for role in roles:
            dag_roles.append(role.get("name"))
        return dag_roles

    @task()
    def permissions_by_role() -> dict:
        """
        Get permissions by role
        Returns:
            dict: Dictionary with permissions by role
        """
        permissions = subprocess.run(
            ["airflow", "roles", "list", "-o", "json", "-p"],
            capture_output=True,
            text=True,
        )
        output = permissions.stdout
        output = json.loads(output)

        permissions_dict_temp = {}

        filter_list = ["Public", "Viewer", "User", "Op", "Admin"]
        output = [item for item in output if item["name"] not in filter_list]

        for item in output:
            name = item["name"]
            resource = item["resource"]
            actions = item["action"].split(",")

            if name not in permissions_dict_temp:
                permissions_dict_temp[name] = []

            permissions_dict_temp[name].append(
                {"resource": resource, "actions": list(set(actions))}
            )

        return permissions_dict_temp

    @task()
    def get_owners() -> list:
        """
        Get owners from all dags
        Returns:
            list: List of owners
        """
        dags = DagBag().dags

        owners_list = []
        for dag_id, dag in dags.items():
            owners_list.append(dag.owner)

        return list(set(owners_list))

    @task()
    def create_roles(owners, roles_list):
        """
        Create roles in Airflow based on owners
        Args:
            owners (list): List of owners
            roles_list (list): List of roles
        """
        for role in owners:
            if role not in roles_list:
                try:
                    subprocess.run(["airflow", "roles", "create", role])
                    logging.info(f"Creating role: {role}")
                except Exception as e:
                    logging.error(f"Error creating role: {role}: {str(e)}")

    @task()
    def get_dags_by_owner() -> dict:
        """
        Get dags by owner
        Returns:
            dict: Dictionary with dags by owner
        """
        dags = DagBag().dags

        dags_by_owner = {}
        for dag_id, dag in dags.items():
            owner = dag.owner
            if owner not in dags_by_owner:
                dags_by_owner[owner] = []
            dags_by_owner[owner].append(dag_id)

        return dags_by_owner

    @task()
    def assign_generic_permissions_roles(dags):
        """
        Assign generic permissions to roles
        Args:
            dags (dict): Dictionary with dags by owner
        """
        resources_dict = {
            "Website": ["can_read"],
            "DAG Runs": ["can_read", "can_edit", "can_create"],
        }
        roles = list(set(dags.keys()))

        for resource, permission in resources_dict.items():
            for element in permission:
                for role in roles:
                    try:
                        subprocess.run(
                            [
                                "airflow",
                                "roles",
                                "add-perms",
                                role,
                                "-a",
                                element,
                                "-r",
                                resource,
                            ]
                        )

                        logging.info(
                            f"Assigning {resource}:{element} permissions to {role}"
                        )
                    except:
                        logging.info(
                            f"Error assigning {resource}:{element} permissions to {role}"
                        )

    @task()
    def get_dags_by_owner_interface() -> dict:
        """
        Get dags by owner from interface
        Returns:
            dict: Dictionary with dags by owner from interface
        """
        result = subprocess.run(
            ["airflow", "roles", "list", "-o", "json", "-p"],
            capture_output=True,
            text=True,
            check=True,
        )

        roles = json.loads(result.stdout)
        dag_roles = {}

        for role in roles:
            if role.get("resource").startswith("DAG:"):
                role_name = role.get("name")
                dag_name = role.get("resource")

                if role_name not in dag_roles:
                    dag_roles[role_name] = []
                dag_roles[role_name].append(dag_name)

        return dag_roles

    @task()
    def assign_permissions_dag(dags_info, owners_interface_dict):
        """
        Assign permissions to dags
        Args:
            dags_info (dict): Dictionary with dags by owner
            owners_interface_dict (dict): Dictionary with dags by owner from Airflow interface
        """
        for owner, dags in dags_info.items():
            for dag_id in dags:

                for interface_owner, interface_dag in owners_interface_dict.items():
                    for dag in interface_dag:

                        if dag_id in dag:
                            current_owner = interface_owner

                            if current_owner == owner:
                                logging.info(
                                    f"Permission for DAG {dag_id} is already correctly assigned to {owner}"
                                )
                                continue
                            try:
                                subprocess.run(
                                    [
                                        "airflow",
                                        "roles",
                                        "add-perms",
                                        owner,
                                        "-a",
                                        "can_read",
                                        "can_edit",
                                        "can_create",
                                        "-r",
                                        f"DAG:{dag_id}",
                                    ],
                                    check=True,
                                )
                                logging.info(
                                    f"Assigned permissions to {owner} for DAG {dag_id}"
                                )
                            except subprocess.CalledProcessError:
                                logging.error(
                                    f"Error assigning permissions to {owner} for DAG {dag_id}"
                                )

    @task()
    def add_users_to_roles():
        """
        Add users to roles based on the file users.yaml
        """
        path = "dags/users.yaml"
        with open(path, "r") as file:
            users_dict = yaml.safe_load(file)

        for role, users in users_dict.items():
            for user in users:
                try:
                    subprocess.run(
                        ["airflow", "users", "add-role", "-r", role, "-e", user]
                    )
                    logging.info(f"Adding user {user} to role {role}")
                except:
                    logging.info(f"Error adding user {user} to role {role}")

    owners_list = get_owners()
    roles_list = list_roles()
    dags_by_owner = get_dags_by_owner()
    permissions_list_by_role = permissions_by_role()
    get_dags_by_owner_interfaces = get_dags_by_owner_interface()

    create_roles(
        owners_list, roles_list
    ) >> permissions_list_by_role >> assign_generic_permissions_roles(
        dags_by_owner
    ) >> assign_permissions_dag(
        dags_by_owner, get_dags_by_owner_interfaces
    ) >> add_users_to_roles()


end = manage_airflow_roles()
