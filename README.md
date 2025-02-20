# Role Manager DAG in Airflow

<img src="https://img.shields.io/badge/python-3.8.10-blue"/> <img src="https://img.shields.io/badge/airflow-2.10.4-blue">

## 1. Description

This project was built to create an Airflow DAG that manages Airflow roles based on DAG owners.  


## 2. Installation

You can clone this repository using the code below: 

```
git clone https://github.com/camila-marquess/airflow-manager-roles-dag.git
```

Before running Airflow, make sure Docker is installed on your OS. If not, follow these steps based on your OS: [Installing Docker Compose](https://docs.docker.com/desktop/install/windows-install/).

To start Airflow, follow the steps described in the [documentation](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html) and then run: 

```
docker-compose up -d
```

You can then view the Airflow UI by accessing `localhost:8080` on your browser. The default login and password are: `airflow`.

To stop the containers, you can run: 

```
docker-compose down
```

I've published a Medium article about this project. You can read it [here]().
