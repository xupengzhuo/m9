
runtime_sets=() # runtime full name

do_dist(){
  echo "start dist $1" 
  IFS=. read -r prj rt <<< $1
  # echo $prj ---- $rt
  m9 build $1
  m9 dist -b $1
  dir_user=$(m9 show $prj | python -c 'import json,sys; print(json.load(sys.stdin)["project_dir"]);')/dist
  cp -rf $dir_user ./packages/$prj
}

do_deploy(){
    echo "start deploy $1"
    IFS=. read -r prj rt <<< $1

    m9 deploy ./packages/$prj
}


batch_dist(){
  for rt in "${runtime_sets[@]}"; do
    do_dist $rt
  done
  tar -czvf ./packages.tar.gz ./packages
}

batch_deploy(){
  for rt in "${runtime_sets[@]}"; do
    do_deploy $rt
  done
  tar -xzvf ./packages.tar.gz
}

# batch_dist
# batch_deploy