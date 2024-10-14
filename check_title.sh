#!/bin/bash

check_title() {
  msg=$1
  if [ ${#msg} -gt 50 ]
  then
    if ! echo $msg | grep -qP '^Merge'
    then
      echo "Commit title is too long: ${#msg}"
      return 1
    fi
  fi
  H1="CODESTYLE|REVIEW|CORE|UTIL|TEST|API|DOCS|TOOLS|BUILD|MC|EC|SCHEDULE|TOPO"
  H2="CI|CL/|TL/|MC/|EC/|UCP|SHM|NCCL|SHARP|BASIC|HIER|CUDA|CPU|EE|RCCL|ROCM|SELF|MLX5"
  if ! echo $msg | grep -qP '^Merge |^'"(($H1)|($H2))"'+: \w'
  then
    echo "Wrong header"
    return 1
  fi
  if [ "${msg: -1}" = "." ]
  then
    echo "Dot at the end of title"
    return 1
  fi
  return 0
}
MSG=$(head -n 1 $1)
echo $MSG
if check_title "$MSG"
then
echo "Good commit title: '$MSG'"
else
echo "Bad commit title: '$MSG'"
exit 1
fi
