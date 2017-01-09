#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <fcntl.h>
#include <dirent.h>
#include <linux/input.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/select.h>
#include <sys/time.h>
#include <termios.h>
#include <signal.h>

char *get_device_name(int fd) {
  char *name = calloc(256, sizeof(char));
  ioctl(fd, EVIOCGNAME(sizeof(char)*256), name);
  return name;
}

char *get_device_location(int fd) {
  char *b = calloc(256, sizeof(char));
  ioctl(fd, EVIOCGPHYS(sizeof(char)*256), b);
  return b;
}

char *get_device_uid(int fd) {
  char *b = calloc(256, sizeof(char));
  ioctl(fd, EVIOCGUNIQ(sizeof(char)*256), b);
  return b;
}

struct input_event *read_event(int fd, int *count) {
  struct input_event *ev = malloc(sizeof(struct input_event) * 64);
  int rdlen = read(fd, ev, sizeof(struct input_event) * 64);
  if (rdlen < sizeof(struct input_event)) {
    free(ev);
    *count = -1;
    return NULL;
  }
  *count = rdlen/sizeof(struct input_event);
  return ev;
}

int inspect_device(char *device) {
  int fd = open(device, O_RDONLY);
  if (fd == -1) {
    fprintf(stderr, "failed to open %s.\n", device);
    return 1;
  }
  char *name = get_device_name(fd);
  char *loc = get_device_location(fd);
  char *uid = get_device_uid(fd);

  printf("%s @ %s (%s)\n",name,loc,uid);

  free(name);
  free(loc);
  free(uid);
  return 0;
}

int listen_device(char *device) {
  int fd;
  
  if ((fd = open(device, O_RDONLY)) == -1) {
    fprintf(stderr, "%s is not a vaild device.\n", device);
    return 1;
  }

  char *name = get_device_name(fd); 
  printf("listening to: %s (%s)\n", device, name);
  free(name);

  while (1) {
    int count = 0;
    struct input_event *ev = read_event(fd, &count);     
    if (count == -1) {
       fprintf(stderr, "failed to read from: %s\n", device);
       if (ev) free(ev);
       return 1;     
    }

    for (int i = 0; i < count; i++) {
      printf("event type %d, code %d, value, %d\n", ev[i].type, ev[i].code, ev[i].value);
    }
  }
 
  return 0;
}
 
int main(int argc, char *argv[]) {
  if ((getuid ()) != 0)
    fprintf(stderr, "%s: WARNING: not running as root.\n",argv[0]);

  if (argc > 1) {
    if (strcmp(argv[1], "inspect") == 0 && argc == 3) return inspect_device(argv[2]);
    else if (strcmp(argv[1], "listen") == 0 && argc == 3) return listen_device(argv[2]);
  }

  fprintf(stderr, "Invalid arguments.\n");
  return 1;
} 

// TODO: kb backlight flash visual bell


