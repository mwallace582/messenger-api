FROM archlinux
COPY messenger_api.py /
COPY tests.py /
COPY requirements.txt /
COPY schema.sql /
RUN pacman -Syy
RUN pacman -S sqlite3 python3 python-pip jq --noconfirm
RUN pip install -r requirements.txt
EXPOSE 5000
CMD ./messenger_api.py
