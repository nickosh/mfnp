presendCommand = """//COMMAND  JOB (USER1),&SYSUID,CLASS=A,NOTIFY=&SYSUID,REGION=0M
//CMD    EXEC PGM=COMMAND
//SYSIN  DD *
v XX00,online
/*"""