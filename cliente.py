#	Fundamentos de Internet  GITT 2017/18
#	Universidad de Sevilla
#	Sergio Palacios Dominguez
#	Cliente

import socket
import sys
import os
import hashlib
import select
import os.path

#	Devuelve la huella MD5 del fichero pasado por parametro
#	Param:	fname (nombre del fichero)
#	Return:	huella MD5
def md5(fname):
	hash_md5 = hashlib.md5()
	with open(fname, "rb") as f:
		for chunk in iter(lambda: f.read(4096), b""):
			hash_md5.update(chunk)
			return hash_md5.hexdigest()

#	Comprobacion del numero de argumentos recibidos
#	argv[0] == cliente.py
#	argv[1] == "filename"
if len(sys.argv) != 2:
	print("Error. Uso: cliente [fichero]")
	sys.exit()

Fconf = open("config.txt")
Indice = 0
Fcontent = sys.argv[1]
Lines = Fconf.readlines()	# Array con todas las lineas del fichero de configuracion

#	Comprobacion del numero de lineas y existencia del fichero de configuracion
if len(Lines) == 0 or os.path.isfile("config.txt") == False:
	print("Error: no hay servidores o fichero de configuracion")
	sys.exit()

#	Comprobacion existencia fichero a enviar
if os.path.isfile(Fcontent) == False:
	print("Error. fichero " + Fcontent + " inexistente")
	sys.exit()

#	Ejecucion por cada linea del fichero de configuracion
while(Indice < len(Lines)):

	S_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)	# Creacion del socket UDP

	Host = Lines [Indice][0:9]	# Recoge la IP del servidor
	Port = int(Lines [Indice][10:15])	# Recoge el puerto del servidor
	Tam = os.stat(Fcontent).st_size	# Calcula el tamano en Bytes del fichero a enviar
	Msg_info = Fcontent + " " + str(Tam)	# Primer mensaje enviado al servidor
	Error = False
	S_udp.sendto(Msg_info,(Host,Port))

	#	Timeout servidor (3 segundos)
	rlist, wlist, elist = select.select( [S_udp], [], [], 3)
	if [rlist, wlist, elist] == [ [], [], [] ]:
		print ("Error: no hay respuesta por parte del servidor " + Host + ' en el puerto ' + str(Port))
		S_udp.close()
	else:
		for sock in rlist:
			Ans, (Host,Port) = S_udp.recvfrom(100)	# Recoge la primera respuesta del servidor("ok", "no")
			
		if Ans == "no":
			print("Error. El servidor " + Host +" no acepta el fichero")
			S_udp.close()
		else:
			while(Error != True):
				Fcontent_op = open(Fcontent)
				Content = Fcontent_op.read()	# Lee el contenido del fichero a transmitir
				Fcontent_op.close()
				
				S_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)	# Creacion del socket TCP
				S_tcp.connect((Host,Port))	# Conexion TCP al servidor con IP: Host y Puerto: Port

				try:
					S_tcp.sendall(Content)	# Envio del contenido del fichero a transmitir al servidor
					
					rlist, wlist, elist = select.select ( [S_tcp], [], [], 10)
					#	Timeout servidor (10 sgundos)
					if [rlist, wlist, elist] == [ [], [], [] ]:
						print("Error en la transferencia con servidor " + Host)
						Error = True
					else:
						for sock in rlist:
							Ans_2 = S_tcp.recv(1024)	# Recoge la segunda respuesta("transfer done", nada)

							if(Ans_2 == "transfer done"):
								S_tcp.close()	# Cierre de conexion TCP
								
								S_udp.sendto(md5(Fcontent),(Host,Port))	# Envio MD5 al servidor
								rlist, wlist, elist = select.select( [S_udp], [], [], 10)
								#	Timeout servidor (10 segundos)
								if [rlist, wlist, elist] == [ [], [], [], 10]:
									print("Error en la copia del fichero en el servidor " + Host  + " . Finalizado el intento")
									Error = True
								else:
									Ans_3, (Host, Port) = S_udp.recvfrom(100)	# Recoge la tercera respuesta("mdsum5 ok", "md5sum error")

									if ("md5sum ok" == Ans_3):
										print("Copia de fichero en el servidor " + Host +" correcta")
										S_udp.close()	# Cierre conexion UDP
										Error = True	# No ocurre error, pero hay que pasar al siguiente server
									if ("md5sum error" == Ans_3):
										print("Error en la copia del fichero en el servidor " + Host +" . Se vuelve a intentar")

				except socket.error, msg:
					print ('Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
					print("No se ha conectado o enviado el fichero al servidor")
					sys.exit()
	
	Indice += 1

sys.exit()