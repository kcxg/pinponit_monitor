FROM harbor.enn.cn/devops/ubuntu-with-python:python-3.6-django
RUN mkdir /pinpoint
ADD . /pinpoint
CMD ["python3","/pinpoint/pinpoint.py"]