celery -A task_manager.scheduler worker --concurrency=4 --loglevel=DEBUG &
celery -A task_manager.scheduler beat --loglevel=DEBUG &
wait -n
exit $?