FROM jupyter/scipy-notebook
RUN conda install -r requirements.txt

USER root

EXPOSE 8899

CMD ["notebook"]