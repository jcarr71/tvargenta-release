si más adelante querés restaurar ese backup en otra Pi o entorno limpio:

sudo tar xzvf tvargenta_es_switch_core_2025-10-25_0045.tar.gz -C /
sudo chmod +x /usr/local/bin/*.sh /srv/tvargenta/encoder_reader
sudo systemctl daemon-reload
sudo systemctl enable tvargenta.service
