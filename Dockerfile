# Dockerfile for FermiLib+ProjectQ

# Change the following line to "FROM continuumio/anaconda" to use Python 2
FROM continuumio/anaconda3

USER root

RUN apt install -y g++

RUN pip install git+https://github.com/ProjectQ-Framework/ProjectQ.git

RUN pip install git+https://github.com/ProjectQ-Framework/FermiLib.git

