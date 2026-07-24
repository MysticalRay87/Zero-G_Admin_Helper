import paramiko

# Use the credentials you already have
transport = paramiko.Transport(("66.23.236.138", 8822))
transport.connect(username="MysticalRay87", password="MidgardMaxipfrf2020!!**")
sftp = paramiko.SFTPClient.from_transport(transport)

# Print the contents of your current SFTP home directory
print(sftp.listdir())

sftp.close()
transport.close()