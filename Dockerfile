FROM harbor.enn.cn/devops/ubuntu-with-python:python-3.6-django
RUN mkdir /pinpoint
ADD . /pinpoint
RUN python3 -m pip install -r requirements.txt
CMD ["python3","-m","/pinpoint/pinpoint.py"]